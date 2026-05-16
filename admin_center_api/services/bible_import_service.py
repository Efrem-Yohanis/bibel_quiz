# admin_center_api/services/bible_import_service.py
"""
Admin Bible Import Service - Handles importing Bible texts
"""

import sqlite3
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class BibleImportService:
    """Service for importing Bible texts"""
    
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
    
    def get_or_create_testament(self, book_name: str) -> int:
        """Get or create testament based on book name"""
        nt_books = [
            'Matthew', 'Mark', 'Luke', 'John', 'Acts',
            'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
            'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
            '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
            'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'
        ]
        
        testament_name = 'New' if book_name in nt_books else 'Old'
        
        self.cursor.execute("INSERT OR IGNORE INTO testaments (name) VALUES (?)", (testament_name,))
        self.cursor.execute("SELECT id FROM testaments WHERE name = ?", (testament_name,))
        return self.cursor.fetchone()[0]
    
    def get_or_create_book(self, book_name: str, testament_id: int) -> int:
        """Get or create book"""
        self.cursor.execute(
            "INSERT OR IGNORE INTO books (name, testament_id) VALUES (?, ?)",
            (book_name, testament_id)
        )
        self.cursor.execute("SELECT id FROM books WHERE name = ?", (book_name,))
        return self.cursor.fetchone()[0]
    
    def get_or_create_chapter(self, book_id: int, chapter_number: int) -> int:
        """Get or create chapter"""
        self.cursor.execute(
            "INSERT OR IGNORE INTO chapters (book_id, chapter_number) VALUES (?, ?)",
            (book_id, chapter_number)
        )
        self.cursor.execute(
            "SELECT id FROM chapters WHERE book_id = ? AND chapter_number = ?",
            (book_id, chapter_number)
        )
        return self.cursor.fetchone()[0]
    
    def get_or_create_verse(self, chapter_id: int, verse_number: int) -> int:
        """Get or create verse"""
        self.cursor.execute(
            "INSERT OR IGNORE INTO verses (chapter_id, verse_number) VALUES (?, ?)",
            (chapter_id, verse_number)
        )
        self.cursor.execute(
            "SELECT id FROM verses WHERE chapter_id = ? AND verse_number = ?",
            (chapter_id, verse_number)
        )
        return self.cursor.fetchone()[0]
    
    def insert_verse_text(self, verse_id: int, language: str, text: str):
        """Insert or update verse text"""
        self.cursor.execute("""
            INSERT OR REPLACE INTO verse_texts (verse_id, language, text)
            VALUES (?, ?, ?)
        """, (verse_id, language, text))
    
    def parse_bible_file(self, file_path: Path, language: str) -> List[Dict]:
        """Parse Bible text file"""
        verses = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        current_book = None
        current_chapter = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('Book:'):
                match = re.search(r'Book:\s+(.+?)\s+\(([A-Z0-9]+)\)', line)
                if match:
                    current_book = match.group(1).strip()
                continue
            
            if line.startswith('Chapter'):
                match = re.search(r'Chapter\s+(\d+)', line, re.IGNORECASE)
                if match:
                    current_chapter = int(match.group(1))
                continue
            
            if line.startswith('==') or line.startswith('--') or line.startswith('***'):
                continue
            
            verse_match = re.match(r'^(\d+)\s*[-:]\s*(.+)$', line)
            if verse_match and current_chapter:
                verse_num = int(verse_match.group(1))
                verse_text = verse_match.group(2).strip()
                
                verses.append({
                    'book_name': current_book,
                    'chapter': current_chapter,
                    'verse': verse_num,
                    'text': verse_text,
                    'language': language
                })
        
        return verses
    
    def import_book(self, file_path: str, language: str) -> Dict:
        """Import a single book"""
        try:
            self.connect()
            
            file_path = Path(file_path)
            verses = self.parse_bible_file(file_path, language)
            
            if not verses:
                return {'success': False, 'message': 'No verses found in file'}
            
            book_name = verses[0]['book_name']
            
            # Get or create testament and book
            testament_id = self.get_or_create_testament(book_name)
            book_id = self.get_or_create_book(book_name, testament_id)
            
            verse_count = 0
            for verse_data in verses:
                chapter_id = self.get_or_create_chapter(book_id, verse_data['chapter'])
                verse_id = self.get_or_create_verse(chapter_id, verse_data['verse'])
                self.insert_verse_text(verse_id, language, verse_data['text'])
                verse_count += 1
            
            self.conn.commit()
            
            return {
                'success': True,
                'message': f'Successfully imported {book_name}',
                'book_name': book_name,
                'verses_imported': verse_count,
                'language': language
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            self.close()
    
    def import_folder(self, folder_path: str, language: str) -> Dict:
        """Import all books from a folder"""
        folder = Path(folder_path)
        txt_files = [f for f in folder.glob("*.txt") if not f.name.startswith('00_')]
        
        results = {
            'success': True,
            'total_files': len(txt_files),
            'imported': [],
            'failed': []
        }
        
        for txt_file in txt_files:
            result = self.import_book(str(txt_file), language)
            if result['success']:
                results['imported'].append(result)
            else:
                results['failed'].append({'file': txt_file.name, 'error': result['message']})
        
        return results
    
    def get_import_status(self) -> Dict:
        """Get current import status"""
        self.connect()
        
        self.cursor.execute("SELECT COUNT(*) FROM books")
        books_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM verses")
        verses_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT language, COUNT(*) FROM verse_texts GROUP BY language")
        verse_texts = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        self.close()
        
        return {
            'books_imported': books_count,
            'verses_imported': verses_count,
            'verse_texts_by_language': verse_texts,
            'languages_available': list(verse_texts.keys())
        }