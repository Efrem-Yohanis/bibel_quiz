# admin_center_api/services/questions_import_service.py
"""
Admin Questions Import Service - Handles importing quiz questions
"""

import sqlite3
import json
import re
from pathlib import Path
from typing import List, Dict

class QuestionsImportService:
    """Service for importing quiz questions"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / 'app' / 'bible_quiz.db'
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
    
    def get_book_id(self, book_name: str) -> int:
        """Get book ID by name"""
        self.cursor.execute("SELECT id FROM books WHERE name LIKE ?", (f'%{book_name}%',))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_chapter_id(self, book_id: int, chapter_number: int) -> int:
        """Get chapter ID by book and chapter number"""
        self.cursor.execute("""
            SELECT id FROM chapters 
            WHERE book_id = ? AND chapter_number = ?
        """, (book_id, chapter_number))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def create_chapter(self, book_id: int, chapter_number: int) -> int:
        """Create a chapter and return its id"""
        self.cursor.execute(
            "INSERT INTO chapters (book_id, chapter_number) VALUES (?, ?)",
            (book_id, chapter_number)
        )
        return self.cursor.lastrowid

    def get_language_id(self, language_code: str) -> int:
        """Return language id for code like 'en'"""
        self.cursor.execute("SELECT id FROM languages WHERE code = ?", (language_code,))
        r = self.cursor.fetchone()
        return r[0] if r else None

    def get_level_id(self, level_number: int) -> int:
        """Return level id for a level number (1,2,3)"""
        self.cursor.execute("SELECT id FROM levels WHERE level_number = ?", (level_number,))
        r = self.cursor.fetchone()
        return r[0] if r else None
    
    def import_questions_json(self, json_file_path: str, language: str) -> Dict:
        """Import questions from JSON file"""
        try:
            self.connect()
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            book_name = Path(json_file_path).stem.replace('questions_', '')
            book_id = self.get_book_id(book_name)
            
            if not book_id:
                return {'success': False, 'message': f'Book "{book_name}" not found in database'}

            language_id = self.get_language_id(language)
            if not language_id:
                return {'success': False, 'message': f'Language "{language}" not found in database'}
            
            questions_imported = 0
            
            for q in data.get('questions', []):
                # determine chapter number
                chapter_number = 1
                vr = q.get('verse_reference') or ''
                m = re.search(r"(\d+):", vr)
                if m:
                    chapter_number = int(m.group(1))
                else:
                    chapter_number = int(q.get('chapter', 1))

                chapter_id = self.get_chapter_id(book_id, chapter_number)
                if not chapter_id:
                    chapter_id = self.create_chapter(book_id, chapter_number)

                # level id
                level_num = q.get('level', 1)
                try:
                    level_num = int(level_num)
                except Exception:
                    level_num = 1
                level_id = self.get_level_id(level_num) or self.get_level_id(1)

                correct_option = q.get('correct_answer') or q.get('correct_option') or 'A'
                # if correct_option is full text, try to map to label when options is dict
                options_data = q.get('options', {})

                # Insert question
                self.cursor.execute("""
                    INSERT INTO questions (book_id, chapter_id, level_id, correct_option, verse_reference)
                    VALUES (?, ?, ?, ?, ?)
                """, (book_id, chapter_id, level_id, correct_option, vr))
                question_id = self.cursor.lastrowid

                if not question_id:
                    # fallback: try to fetch existing question
                    self.cursor.execute("SELECT id FROM questions WHERE book_id=? AND chapter_id=? AND verse_reference=? LIMIT 1",
                                        (book_id, chapter_id, vr))
                    r = self.cursor.fetchone()
                    question_id = r[0] if r else None

                if not question_id:
                    # cannot continue without question id
                    continue

                # Insert or replace question text
                self.cursor.execute("""
                    INSERT OR REPLACE INTO question_texts (question_id, language_id, text)
                    VALUES (?, ?, ?)
                """, (question_id, language_id, q.get('question', '')))

                # handle options formats: dict {A: text} or list of {label,text}
                if isinstance(options_data, dict):
                    items = list(options_data.items())
                elif isinstance(options_data, list):
                    items = []
                    for opt in options_data:
                        if isinstance(opt, dict):
                            lbl = opt.get('label') or opt.get('option')
                            txt = opt.get('text') or opt.get('value')
                            items.append((lbl, txt))
                else:
                    items = []

                for label, text in items:
                    if not label:
                        continue
                    # Normalize label to single char
                    label_str = str(label).strip()
                    self.cursor.execute("INSERT INTO options (question_id, label) VALUES (?, ?)", (question_id, label_str))
                    option_id = self.cursor.lastrowid
                    if option_id:
                        self.cursor.execute("INSERT INTO option_texts (option_id, language_id, text) VALUES (?, ?, ?)",
                                            (option_id, language_id, text))

                # Insert explanation
                if q.get('explanation'):
                    self.cursor.execute("INSERT OR REPLACE INTO explanations (question_id, language_id, text) VALUES (?, ?, ?)",
                                        (question_id, language_id, q.get('explanation', '')))

                questions_imported += 1
            
            self.conn.commit()
            
            return {
                'success': True,
                'message': f'Successfully imported {questions_imported} questions for {book_name}',
                'book_name': book_name,
                'questions_imported': questions_imported,
                'language': language
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            self.close()
    
    def import_folder(self, folder_path: str, language: str) -> Dict:
        """Import all question JSON files from a folder"""
        folder = Path(folder_path)
        json_files = list(folder.glob("*.json"))
        
        results = {
            'success': True,
            'total_files': len(json_files),
            'imported': [],
            'failed': []
        }
        
        for json_file in json_files:
            result = self.import_questions_json(str(json_file), language)
            if result['success']:
                results['imported'].append(result)
            else:
                results['failed'].append({'file': json_file.name, 'error': result['message']})
        
        return results
    
    def get_questions_status(self) -> Dict:
        """Get current questions import status"""
        self.connect()
        
        self.cursor.execute("SELECT COUNT(*) FROM questions")
        questions_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT language, COUNT(*) FROM question_texts GROUP BY language")
        question_texts = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        self.close()
        
        return {
            'total_questions': questions_count,
            'questions_by_language': question_texts
        }