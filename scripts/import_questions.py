# scripts/import_questions.py
"""
Complete Questions Import Script for all testaments and languages
Uses normalized tables: languages, levels, books, chapters
"""

import sqlite3
import json
import re
from pathlib import Path
from typing import Dict, Optional

# Set the correct base path
BASE_PATH = Path(__file__).parent.parent
APP_PATH = BASE_PATH / 'app'
DB_PATH = APP_PATH / 'bible_quiz.db'

print(f"Base path: {BASE_PATH}")
print(f"App path: {APP_PATH}")
print(f"Database path: {DB_PATH}")

class CompleteQuestionsImporter:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.conn = None
        self.cursor = None
        
        # Language mapping (folder name to language code)
        self.language_map = {
            'amharic_bible': 'am',
            'english_bible': 'en',
            'oromifa_bible': 'or'
        }
        
        # Book name mapping (JSON book name -> Database English book name)
        self.book_name_map = {
            # Amharic to English
            'ዘፍጥረት': 'Genesis',
            'ዘጸአት': 'Exodus',
            'ዘሌዋውያን': 'Leviticus',
            'ዘኁልቁ': 'Numbers',
            'ዘዳግም': 'Deuteronomy',
            'ኢያሱ': 'Joshua',
            'መሳፍንት': 'Judges',
            'ሩት': 'Ruth',
            # Oromo to English
            'Uumama': 'Genesis',
            'Baʼuu': 'Exodus',
            'Lewweesssa': 'Leviticus',
            'Lakkoofsa': 'Numbers',
            'Keessummeessa': 'Deuteronomy',
            'Yoh’sheeʼaa': 'Joshua',
            'Abbootii Murtii': 'Judges',
            'Ruuʼa': 'Ruth',
            # English to English
            'Genesis': 'Genesis',
            'Exodus': 'Exodus',
            'Leviticus': 'Leviticus',
            'Numbers': 'Numbers',
            'Deuteronomy': 'Deuteronomy',
            'Joshua': 'Joshua',
            'Judges': 'Judges',
            'Ruth': 'Ruth',
        }
        
        # Level name to number mapping
        self.level_name_to_number = {
            'Easy': 1, 'easy': 1, 'EASY': 1,
            'Medium': 2, 'medium': 2, 'MEDIUM': 2,
            'Hard': 3, 'hard': 3, 'HARD': 3,
            'ቀላል': 1, 'መካከለኛ': 2, 'ከባድ': 3,
            'Salphaa': 1, 'Giddugaleessa': 2, 'Cimaa': 3
        }
        
        # Language code to ID cache
        self.language_ids = {}
        
        # Level number to ID cache
        self.level_ids = {}
        
        # Book name to ID cache
        self.book_ids = {}
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
    
    def get_language_id(self, language_code: str) -> Optional[int]:
        """Get language ID from language code"""
        if language_code in self.language_ids:
            return self.language_ids[language_code]
        
        self.cursor.execute("SELECT id FROM languages WHERE code = ?", (language_code,))
        result = self.cursor.fetchone()
        
        if result:
            self.language_ids[language_code] = result[0]
            return result[0]
        
        print(f"⚠️ Language '{language_code}' not found in database")
        return None
    
    def get_level_id(self, level_number: int) -> Optional[int]:
        """Get level ID from level number"""
        if level_number in self.level_ids:
            return self.level_ids[level_number]
        
        self.cursor.execute("SELECT id FROM levels WHERE level_number = ?", (level_number,))
        result = self.cursor.fetchone()
        
        if result:
            self.level_ids[level_number] = result[0]
            return result[0]
        
        print(f"⚠️ Level number '{level_number}' not found in database")
        return None
    
    def get_book_id(self, book_name: str) -> Optional[int]:
        """Get book ID by name (case-insensitive) with mapping"""
        mapped_name = self.book_name_map.get(book_name, book_name)
        
        cache_key = mapped_name.lower()
        if cache_key in self.book_ids:
            return self.book_ids[cache_key]
        
        self.cursor.execute("SELECT id FROM books WHERE LOWER(name) = LOWER(?)", (mapped_name,))
        result = self.cursor.fetchone()
        
        if result:
            self.book_ids[cache_key] = result[0]
            return result[0]
        
        self.cursor.execute("SELECT id FROM books WHERE name LIKE ?", (f'%{mapped_name}%',))
        result = self.cursor.fetchone()
        
        if result:
            self.book_ids[cache_key] = result[0]
            return result[0]
        
        print(f"⚠️ Book '{book_name}' (mapped to '{mapped_name}') not found")
        return None
    
    def get_or_create_chapter(self, book_id: int, chapter_number: int) -> int:
        """Get or create chapter"""
        self.cursor.execute(
            "SELECT id FROM chapters WHERE book_id = ? AND chapter_number = ?",
            (book_id, chapter_number)
        )
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        self.cursor.execute(
            "INSERT INTO chapters (book_id, chapter_number) VALUES (?, ?)",
            (book_id, chapter_number)
        )
        return self.cursor.lastrowid
    
    def extract_chapter_from_reference(self, verse_reference: str) -> int:
        """Extract chapter number from verse reference"""
        match = re.search(r'(\d+):', verse_reference)
        if match:
            return int(match.group(1))
        return 1
    
    def parse_options(self, options_data):
        """Parse options whether they are dict or list"""
        options_dict = {}
        
        if isinstance(options_data, dict):
            # Already a dictionary
            return options_data
        elif isinstance(options_data, list):
            # Convert list to dictionary
            for opt in options_data:
                if isinstance(opt, dict):
                    label = opt.get('label', opt.get('letter', ''))
                    text = opt.get('text', opt.get('value', ''))
                    if label and text:
                        options_dict[label] = text
                elif isinstance(opt, (list, tuple)) and len(opt) == 2:
                    options_dict[opt[0]] = opt[1]
            return options_dict
        else:
            return {}
    
    def import_questions_from_json(self, json_file_path: Path, language_code: str) -> Dict:
        """Import questions from JSON file"""
        print(f"    📖 Processing {json_file_path.name}...")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"      ❌ JSON parse error: {e}")
            return {
                'success': False,
                'error': f'JSON parse error: {e}',
                'book_name': json_file_path.stem
            }
        
        metadata = data.get('metadata', {})
        questions = data.get('questions', [])
        
        if not questions:
            print(f"      ⚠ No questions found in file")
            return {
                'success': False,
                'error': 'No questions found',
                'book_name': json_file_path.stem
            }
        
        # Get book name
        book_name = metadata.get('book')
        if not book_name:
            book_name = json_file_path.stem.replace('questions_', '')
        
        # Get IDs
        book_id = self.get_book_id(book_name)
        if not book_id:
            return {
                'success': False,
                'error': f'Book "{book_name}" not found',
                'book_name': book_name
            }
        
        language_id = self.get_language_id(language_code)
        if not language_id:
            return {
                'success': False,
                'error': f'Language "{language_code}" not found',
                'book_name': book_name
            }
        
        questions_imported = 0
        questions_updated = 0
        questions_skipped = 0
        
        for q in questions:
            try:
                question_id = q.get('id')
                level_value = q.get('level', 1)
                
                # Convert level to number
                if isinstance(level_value, str):
                    level_number = self.level_name_to_number.get(level_value, 1)
                else:
                    level_number = level_value
                
                verse_reference = q.get('verse_reference', '')
                question_text = q.get('question', '')
                correct_answer = q.get('correct_answer', q.get('correct_option', 'A'))
                
                # Parse options (handles both dict and list)
                options = self.parse_options(q.get('options', {}))
                explanation = q.get('explanation', '')
                
                # Get level ID
                level_id = self.get_level_id(level_number)
                if not level_id:
                    print(f"      ⚠ Level {level_value} not found, skipping")
                    questions_skipped += 1
                    continue
                
                # Extract chapter number
                chapter_number = self.extract_chapter_from_reference(verse_reference)
                chapter_id = self.get_or_create_chapter(book_id, chapter_number)
                
                # Check if question exists
                self.cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
                existing = self.cursor.fetchone()
                
                if existing:
                    self.cursor.execute("""
                        UPDATE questions 
                        SET book_id = ?, chapter_id = ?, level_id = ?, 
                            correct_option = ?, verse_reference = ?
                        WHERE id = ?
                    """, (book_id, chapter_id, level_id, correct_answer, verse_reference, question_id))
                    questions_updated += 1
                else:
                    self.cursor.execute("""
                        INSERT INTO questions (id, book_id, chapter_id, level_id, correct_option, verse_reference)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (question_id, book_id, chapter_id, level_id, correct_answer, verse_reference))
                    questions_imported += 1
                
                # Insert question text
                self.cursor.execute("""
                    INSERT OR REPLACE INTO question_texts (question_id, language_id, text)
                    VALUES (?, ?, ?)
                """, (question_id, language_id, question_text))
                
                # Insert options
                for label, text in options.items():
                    self.cursor.execute("INSERT OR IGNORE INTO options (question_id, label) VALUES (?, ?)", 
                                      (question_id, label))
                    self.cursor.execute("SELECT id FROM options WHERE question_id = ? AND label = ?", 
                                      (question_id, label))
                    option_row = self.cursor.fetchone()
                    if option_row:
                        self.cursor.execute("""
                            INSERT OR REPLACE INTO option_texts (option_id, language_id, text)
                            VALUES (?, ?, ?)
                        """, (option_row[0], language_id, text))
                
                # Insert explanation
                if explanation:
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO explanations (question_id, language_id, text)
                        VALUES (?, ?, ?)
                    """, (question_id, language_id, explanation))
                    
            except Exception as e:
                print(f"      ⚠ Error processing question {q.get('id', 'unknown')}: {e}")
                questions_skipped += 1
                continue
        
        self.conn.commit()
        
        return {
            'success': True,
            'book_name': book_name,
            'language': language_code,
            'questions_imported': questions_imported,
            'questions_updated': questions_updated,
            'questions_skipped': questions_skipped,
            'total_questions': len(questions)
        }
    
    def import_all_questions(self):
        """Import all questions from all folders"""
        
        print("\n" + "="*60)
        print("📝 IMPORTING ALL QUESTIONS")
        print("="*60)
        
        question_paths = [
            (APP_PATH / 'each_book_qestion_json_file' / 'Old_Testament' / 'amharic_bible', 'am'),
            (APP_PATH / 'each_book_qestion_json_file' / 'Old_Testament' / 'english_bible', 'en'),
            (APP_PATH / 'each_book_qestion_json_file' / 'Old_Testament' / 'oromifa_bible', 'or'),
            (APP_PATH / 'each_book_qestion_json_file' / 'New_Testament' / 'amharic_bible', 'am'),
            (APP_PATH / 'each_book_qestion_json_file' / 'New_Testament' / 'english_bible', 'en'),
            (APP_PATH / 'each_book_qestion_json_file' / 'New_Testament' / 'oromifa_bible', 'or'),
        ]
        
        stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'by_language': {'am': 0, 'en': 0, 'or': 0},
            'details': []
        }
        
        for folder_path, language_code in question_paths:
            if not folder_path.exists():
                continue
            
            json_files = list(folder_path.glob("*.json"))
            
            if not json_files:
                continue
            
            lang_name = {'am': 'Amharic', 'en': 'English', 'or': 'Oromo'}.get(language_code, language_code)
            print(f"\n📁 Processing {lang_name} ({language_code})")
            print("-" * 40)
            
            for json_file in json_files:
                stats['total_files'] += 1
                
                try:
                    result = self.import_questions_from_json(json_file, language_code)
                    
                    if result.get('success'):
                        stats['successful'] += 1
                        stats['by_language'][language_code] += result.get('questions_imported', 0)
                        stats['details'].append(result)
                        print(f"    ✅ {result['book_name']}: {result['questions_imported']} new, {result['questions_updated']} updated, {result['questions_skipped']} skipped")
                    else:
                        stats['failed'] += 1
                        print(f"    ❌ {result.get('book_name', json_file.name)}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    stats['failed'] += 1
                    print(f"    ❌ Error importing {json_file.name}: {e}")
        
        return stats
    
    def verify_import(self):
        """Verify the import results"""
        print("\n" + "="*60)
        print("📊 VERIFYING IMPORT")
        print("="*60)
        
        self.cursor.execute("SELECT COUNT(*) FROM questions")
        questions_count = self.cursor.fetchone()[0]
        print(f"✓ Total Questions: {questions_count}")
        
        self.cursor.execute("""
            SELECT l.code, COUNT(qt.id) as count
            FROM question_texts qt
            JOIN languages l ON qt.language_id = l.id
            GROUP BY l.id
            ORDER BY l.id
        """)
        print(f"\n✓ Question Texts by Language:")
        for code, count in self.cursor.fetchall():
            print(f"   {code}: {count}")
        
        self.cursor.execute("""
            SELECT l.level_number, COUNT(q.id) as count
            FROM questions q
            JOIN levels l ON q.level_id = l.id
            GROUP BY l.id
            ORDER BY l.level_number
        """)
        print(f"\n✓ Questions by Level:")
        for level, count in self.cursor.fetchall():
            print(f"   Level {level}: {count}")
        
        self.cursor.execute("SELECT COUNT(*) FROM options")
        options_count = self.cursor.fetchone()[0]
        print(f"\n✓ Total Options: {options_count}")
    
    def run(self):
        """Run complete import"""
        print("="*60)
        print("🚀 COMPLETE QUESTIONS IMPORTER")
        print("="*60)
        
        try:
            self.connect()
            print(f"✓ Connected to database: {self.db_path}")
            
            required_tables = ['languages', 'levels', 'books', 'chapters']
            for table in required_tables:
                self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not self.cursor.fetchone():
                    print(f"❌ Table '{table}' not found. Run 'python app/init_db.py' first.")
                    return
            
            stats = self.import_all_questions()
            
            print("\n" + "="*60)
            print("📊 IMPORT SUMMARY")
            print("="*60)
            print(f"Total files: {stats['total_files']}")
            print(f"✅ Successful: {stats['successful']}")
            print(f"❌ Failed: {stats['failed']}")
            
            self.verify_import()
            
            print("\n✅ IMPORT COMPLETE!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()


if __name__ == "__main__":
    importer = CompleteQuestionsImporter()
    importer.run()