# app/services/bible_service.py
"""
Bible Service - Manages Bible text retrieval
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / 'bible_quiz.db'

class BibleService:
    """Service for Bible text operations"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_testaments(self) -> List[Dict]:
        """Get list of all testaments (Old and New)"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM testaments ORDER BY id")
        testaments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return testaments
    
    def get_books_by_testament(self, testament_name: str) -> List[Dict]:
        """Get list of books by testament name (Old or New)"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.id, b.name, t.name as testament,
                   COUNT(DISTINCT c.id) as chapters,
                   COUNT(DISTINCT v.id) as verses
            FROM books b
            JOIN testaments t ON b.testament_id = t.id
            LEFT JOIN chapters c ON c.book_id = b.id
            LEFT JOIN verses v ON v.chapter_id = c.id
            WHERE t.name = ?
            GROUP BY b.id
            ORDER BY b.id
        """, (testament_name,))
        
        books = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return books
    
    def get_books_by_testament_with_language(self, testament_name: str, language: str = 'en') -> List[Dict]:
        """Get list of books by testament with chapter counts for specific language"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT b.id, b.name,
                   COUNT(DISTINCT c.id) as total_chapters
            FROM books b
            JOIN testaments t ON b.testament_id = t.id
            LEFT JOIN chapters c ON c.book_id = b.id
            WHERE t.name = ?
            GROUP BY b.id
            ORDER BY b.id
        """, (testament_name,))
        
        books = cursor.fetchall()
        conn.close()
        
        return [
            {
                'book_id': book['id'],
                'book_name': book['name'],
                'total_chapters': book['total_chapters'] or 0
            }
            for book in books
        ]
    
    def get_book_full_content(self, book_name: str, language: str = 'en') -> Dict:
        """Get full content of a specific book with book info"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get book info
        cursor.execute("""
            SELECT b.id, b.name, t.name as testament,
                   COUNT(DISTINCT c.id) as total_chapters,
                   COUNT(DISTINCT v.id) as total_verses
            FROM books b
            JOIN testaments t ON b.testament_id = t.id
            LEFT JOIN chapters c ON c.book_id = b.id
            LEFT JOIN verses v ON v.chapter_id = c.id
            WHERE b.name = ? OR b.name LIKE ? OR b.name LIKE ?
            GROUP BY b.id
        """, (book_name, f'%{book_name}%', f'{book_name}%'))
        
        book_info = cursor.fetchone()
        
        if not book_info:
            conn.close()
            return {'error': f'Book "{book_name}" not found'}
        
        # Get all chapters and verses
        cursor.execute("""
            SELECT c.chapter_number, v.verse_number, vt.text
            FROM chapters c
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE c.book_id = ? AND vt.language = ?
            ORDER BY c.chapter_number, v.verse_number
        """, (book_info['id'], language))
        
        verses = cursor.fetchall()
        conn.close()
        
        # Organize by chapter
        chapters_content = {}
        for verse in verses:
            chapter = verse['chapter_number']
            if chapter not in chapters_content:
                chapters_content[chapter] = []
            chapters_content[chapter].append({
                'verse': verse['verse_number'],
                'text': verse['text']
            })
        
        return {
            'book_info': {
                'id': book_info['id'],
                'name': book_info['name'],
                'testament': book_info['testament'],
                'total_chapters': book_info['total_chapters'] or 0,
                'total_verses': book_info['total_verses'] or 0
            },
            'chapters': [
                {
                    'chapter': chapter,
                    'verses': verses_data
                }
                for chapter, verses_data in sorted(chapters_content.items())
            ]
        }
    
    def get_book_chapters(self, book_name: str) -> Dict:
        """Get list of chapters in a book with verse counts"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get book info
        cursor.execute("""
            SELECT id, name FROM books WHERE name = ? OR name LIKE ? OR name LIKE ?
        """, (book_name, f'%{book_name}%', f'{book_name}%'))
        
        book = cursor.fetchone()
        
        if not book:
            conn.close()
            return {'error': f'Book "{book_name}" not found'}
        
        # Get chapters with verse counts
        cursor.execute("""
            SELECT c.chapter_number, COUNT(v.id) as verse_count
            FROM chapters c
            LEFT JOIN verses v ON v.chapter_id = c.id
            WHERE c.book_id = ?
            GROUP BY c.chapter_number
            ORDER BY c.chapter_number
        """, (book['id'],))
        
        chapters = cursor.fetchall()
        conn.close()
        
        return {
            'book': book['name'],
            'total_chapters': len(chapters),
            'chapters': [
                {
                    'chapter': c['chapter_number'],
                    'verses': c['verse_count'] or 0
                }
                for c in chapters
            ]
        }
    
    def get_book_chapters_with_language(self, book_name: str, language: str = 'en') -> Dict:
        """Get chapters of a book with verse counts for specific language"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get book info
        cursor.execute("""
            SELECT id, name FROM books WHERE name = ? OR name LIKE ? OR name LIKE ?
        """, (book_name, f'%{book_name}%', f'{book_name}%'))
        
        book = cursor.fetchone()
        
        if not book:
            conn.close()
            return {'error': f'Book "{book_name}" not found'}
        
        # Get chapters with verse counts
        cursor.execute("""
            SELECT c.chapter_number, COUNT(v.id) as verse_count
            FROM chapters c
            LEFT JOIN verses v ON v.chapter_id = c.id
            WHERE c.book_id = ?
            GROUP BY c.chapter_number
            ORDER BY c.chapter_number
        """, (book['id'],))
        
        chapters = cursor.fetchall()
        conn.close()
        
        return {
            'book_id': book['id'],
            'book_name': book['name'],
            'total_chapters': len(chapters),
            'chapters': [
                {
                    'chapter': c['chapter_number'],
                    'verses': c['verse_count'] or 0
                }
                for c in chapters
            ]
        }
    
    def get_chapters_content(self, book_name: str, language: str = 'en') -> Dict:
        """Get all chapters content of a book"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get book info
        cursor.execute("SELECT id, name FROM books WHERE name = ? OR name LIKE ?", 
                      (book_name, f'%{book_name}%'))
        book = cursor.fetchone()
        
        if not book:
            conn.close()
            return {'error': f'Book "{book_name}" not found'}
        
        # Get all verses
        cursor.execute("""
            SELECT c.chapter_number, v.verse_number, vt.text
            FROM chapters c
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE c.book_id = ? AND vt.language = ?
            ORDER BY c.chapter_number, v.verse_number
        """, (book['id'], language))
        
        verses = cursor.fetchall()
        conn.close()
        
        # Group by chapter
        chapters_content = {}
        for verse in verses:
            chapter = verse['chapter_number']
            if chapter not in chapters_content:
                chapters_content[chapter] = []
            chapters_content[chapter].append({
                'verse': verse['verse_number'],
                'text': verse['text']
            })
        
        return {
            'book': book['name'],
            'total_chapters': len(chapters_content),
            'chapters': [
                {
                    'chapter': chapter,
                    'verses': verses_data
                }
                for chapter, verses_data in sorted(chapters_content.items())
            ]
        }
    
    def get_chapter_verses(self, book_name: str, chapter: int, language: str = 'en') -> Dict:
        """Get a specific chapter's verses"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get book info
        cursor.execute("SELECT id, name FROM books WHERE name = ? OR name LIKE ?", 
                      (book_name, f'%{book_name}%'))
        book = cursor.fetchone()
        
        if not book:
            conn.close()
            return {'error': f'Book "{book_name}" not found'}
        
        # Get chapter verses
        cursor.execute("""
            SELECT v.verse_number, vt.text
            FROM chapters c
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE c.book_id = ? AND c.chapter_number = ? AND vt.language = ?
            ORDER BY v.verse_number
        """, (book['id'], chapter, language))
        
        verses = cursor.fetchall()
        conn.close()
        
        if not verses:
            return {
                'error': f'Chapter {chapter} not found in {book["name"]}'
            }
        
        return {
            'reference': f'{book["name"]} {chapter}',
            'book': book['name'],
            'chapter': chapter,
            'total_verses': len(verses),
            'verses': [
                {
                    'verse': v['verse_number'],
                    'text': v['text']
                }
                for v in verses
            ]
        }
    
    def get_specific_verse(self, book_name: str, chapter: int, verse: int, language: str = 'en') -> Dict:
        """Get a specific verse"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get book info
        cursor.execute("SELECT id, name FROM books WHERE name = ? OR name LIKE ?", 
                      (book_name, f'%{book_name}%'))
        book = cursor.fetchone()
        
        if not book:
            conn.close()
            return {'error': f'Book "{book_name}" not found'}
        
        # Get verse
        cursor.execute("""
            SELECT vt.text
            FROM chapters c
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE c.book_id = ? AND c.chapter_number = ? 
              AND v.verse_number = ? AND vt.language = ?
        """, (book['id'], chapter, verse, language))
        
        verse_data = cursor.fetchone()
        conn.close()
        
        if not verse_data:
            return {
                'error': f'Verse {book_name} {chapter}:{verse} not found'
            }
        
        return {
            'reference': f'{book["name"]} {chapter}:{verse}',
            'book': book['name'],
            'chapter': chapter,
            'verse': verse,
            'text': verse_data['text']
        }
    
    def get_verse_all_languages(self, book_name: str, chapter: int, verse: int) -> Dict:
        """Get a verse in all available languages"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get book info
        cursor.execute("SELECT id, name FROM books WHERE name = ? OR name LIKE ?", 
                      (book_name, f'%{book_name}%'))
        book = cursor.fetchone()
        
        if not book:
            conn.close()
            return {'error': f'Book "{book_name}" not found'}
        
        # Get verse in all languages
        cursor.execute("""
            SELECT vt.language, vt.text
            FROM chapters c
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE c.book_id = ? AND c.chapter_number = ? AND v.verse_number = ?
        """, (book['id'], chapter, verse))
        
        texts = cursor.fetchall()
        conn.close()
        
        if not texts:
            return {'error': f'Verse {book_name} {chapter}:{verse} not found'}
        
        languages_map = {
            'en': 'English',
            'am': 'Amharic',
            'or': 'Oromo'
        }
        
        result = {
            'reference': f'{book["name"]} {chapter}:{verse}',
            'verses': {}
        }
        
        for t in texts:
            lang_name = languages_map.get(t['language'], t['language'])
            result['verses'][lang_name] = t['text']
        
        return result
    
    def search_verses(self, query: str, language: str = 'en', limit: int = 50) -> List[Dict]:
        """Search for verses containing specific text"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.name as book, c.chapter_number, v.verse_number, vt.text
            FROM verse_texts vt
            JOIN verses v ON vt.verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE vt.language = ? AND vt.text LIKE ?
            LIMIT ?
        """, (language, f'%{query}%', limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'reference': f"{r['book']} {r['chapter_number']}:{r['verse_number']}",
                'book': r['book'],
                'chapter': r['chapter_number'],
                'verse': r['verse_number'],
                'text': r['text']
            }
            for r in results
        ]
    
    def get_random_verse(self, language: str = 'en', testament: Optional[str] = None) -> Dict:
        """Get a random Bible verse"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        if testament:
            cursor.execute("""
                SELECT b.name as book, c.chapter_number, v.verse_number, vt.text
                FROM verse_texts vt
                JOIN verses v ON vt.verse_id = v.id
                JOIN chapters c ON v.chapter_id = c.id
                JOIN books b ON c.book_id = b.id
                JOIN testaments t ON b.testament_id = t.id
                WHERE vt.language = ? AND t.name = ?
                ORDER BY RANDOM()
                LIMIT 1
            """, (language, testament))
        else:
            cursor.execute("""
                SELECT b.name as book, c.chapter_number, v.verse_number, vt.text
                FROM verse_texts vt
                JOIN verses v ON vt.verse_id = v.id
                JOIN chapters c ON v.chapter_id = c.id
                JOIN books b ON c.book_id = b.id
                WHERE vt.language = ?
                ORDER BY RANDOM()
                LIMIT 1
            """, (language,))
        
        verse = cursor.fetchone()
        conn.close()
        
        if not verse:
            return {'error': 'No verses found'}
        
        return {
            'reference': f"{verse['book']} {verse['chapter_number']}:{verse['verse_number']}",
            'book': verse['book'],
            'chapter': verse['chapter_number'],
            'verse': verse['verse_number'],
            'text': verse['text']
        }
    
    def get_verse_of_the_day(self, language: str = 'en') -> Dict:
        """Get verse of the day (based on current date)"""
        # Use day of year to get a consistent verse
        day_of_year = datetime.now().timetuple().tm_yday
        
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.name as book, c.chapter_number, v.verse_number, vt.text
            FROM verse_texts vt
            JOIN verses v ON vt.verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE vt.language = ?
            LIMIT 1 OFFSET ?
        """, (language, day_of_year % 100))
        
        verse = cursor.fetchone()
        conn.close()
        
        if not verse:
            return self.get_random_verse(language)
        
        return {
            'reference': f"{verse['book']} {verse['chapter_number']}:{verse['verse_number']}",
            'book': verse['book'],
            'chapter': verse['chapter_number'],
            'verse': verse['verse_number'],
            'text': verse['text']
        }
    
    def get_bible_stats(self) -> Dict:
        """Get overall Bible statistics"""
        old_testament = self.get_testament_stats('Old')
        new_testament = self.get_testament_stats('New')
        
        return {
            'old_testament': old_testament,
            'new_testament': new_testament,
            'total': {
                'books': old_testament.get('books', 0) + new_testament.get('books', 0),
                'chapters': old_testament.get('chapters', 0) + new_testament.get('chapters', 0),
                'verses': old_testament.get('verses', 0) + new_testament.get('verses', 0)
            }
        }
    
    def get_testament_stats(self, testament: str) -> Dict:
        """Get statistics for a testament"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT b.id) as books,
                COUNT(DISTINCT c.id) as chapters,
                COUNT(DISTINCT v.id) as verses
            FROM testaments t
            JOIN books b ON b.testament_id = t.id
            LEFT JOIN chapters c ON c.book_id = b.id
            LEFT JOIN verses v ON v.chapter_id = c.id
            WHERE t.name = ?
        """, (testament,))
        
        stats = cursor.fetchone()
        conn.close()
        
        return dict(stats) if stats else {'books': 0, 'chapters': 0, 'verses': 0}