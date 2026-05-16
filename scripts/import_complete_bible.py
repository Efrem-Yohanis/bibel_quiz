# scripts/import_complete_bible.py
"""
Complete Bible Import Script - Updated for your folder structure and new schema
"""

import sqlite3
import re
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent
APP_PATH = BASE_PATH / 'app'
DB_PATH = APP_PATH / 'bible_quiz.db'

print(f"Base path: {BASE_PATH}")
print(f"App path: {APP_PATH}")
print(f"Database path: {DB_PATH}")

class CompleteBibleImporter:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.conn = None
        self.cursor = None
        
        # Cache for language IDs
        self.language_ids = {}
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
    
    def get_language_id(self, language_code):
        """Get language ID from language code"""
        if language_code in self.language_ids:
            return self.language_ids[language_code]
        
        self.cursor.execute("SELECT id FROM languages WHERE code = ?", (language_code,))
        result = self.cursor.fetchone()
        if result:
            self.language_ids[language_code] = result[0]
            return result[0]
        
        # Default to English (id=1)
        return 1
    
    def get_or_create_testament(self, book_name):
        """Get or create testament based on book name"""
        nt_books = [
            'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Gospel_of_John', 'Gospel_of_Luke',
            'Gospel_of_Mark', 'Gospel_of_Matthew', 'Romans', '1 Corinthians', '2 Corinthians',
            'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians',
            '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
            'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'
        ]
        
        testament_name = 'New' if book_name in nt_books else 'Old'
        
        self.cursor.execute("INSERT OR IGNORE INTO testaments (name) VALUES (?)", (testament_name,))
        self.cursor.execute("SELECT id FROM testaments WHERE name = ?", (testament_name,))
        return self.cursor.fetchone()[0]
    
    def get_or_create_book(self, book_name, testament_id):
        """Get or create book"""
        self.cursor.execute(
            "INSERT OR IGNORE INTO books (name, testament_id) VALUES (?, ?)",
            (book_name, testament_id)
        )
        self.cursor.execute("SELECT id FROM books WHERE name = ?", (book_name,))
        return self.cursor.fetchone()[0]
    
    def get_or_create_chapter(self, book_id, chapter_number):
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
    
    def get_or_create_verse(self, chapter_id, verse_number):
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
    
    def insert_verse_text(self, verse_id, language_id, text):
        """Insert or update verse text with language_id"""
        self.cursor.execute("""
            INSERT OR REPLACE INTO verse_texts (verse_id, language_id, text)
            VALUES (?, ?, ?)
        """, (verse_id, language_id, text))
    
    def parse_bible_text_file(self, file_path, language_code):
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
            if verse_match and current_chapter and current_book:
                verse_num = int(verse_match.group(1))
                verse_text = verse_match.group(2).strip()
                
                verses.append({
                    'book_name': current_book,
                    'chapter': current_chapter,
                    'verse': verse_num,
                    'text': verse_text,
                    'language_code': language_code
                })
        
        return verses
    
    def import_all_bibles(self):
        """Import all Bible files from all folders"""
        
        print("\n" + "="*60)
        print("📖 IMPORTING ALL BIBLE TEXTS")
        print("="*60)
        
        # Language folder mapping
        languages = {
            'amharic_bible': 'am',
            'english_bible': 'en',
            'oromifa_bible': 'or'
        }
        
        testaments = ['Old_Testament', 'New_Testament']
        
        stats = {
            'total_verses': 0,
            'languages': {'am': 0, 'en': 0, 'or': 0},
            'books': set()
        }
        
        for testament in testaments:
            testament_path = APP_PATH / 'full_bibel_txt_file' / testament
            
            if not testament_path.exists():
                print(f"⚠ Path not found: {testament_path}")
                continue
            
            print(f"\n📁 Processing {testament}/")
            print("-" * 40)
            
            for lang_folder, lang_code in languages.items():
                lang_path = testament_path / lang_folder
                
                if not lang_path.exists():
                    print(f"  ⚠ {lang_folder} not found in {testament}")
                    continue
                
                txt_files = [f for f in lang_path.glob("*.txt") if not f.name.startswith('00_')]
                
                if not txt_files:
                    print(f"  ⚠ No text files found in {lang_folder}")
                    continue
                
                print(f"\n  📚 {lang_folder.upper()} ({lang_code}): {len(txt_files)} files")
                
                for txt_file in txt_files:
                    book_name = txt_file.stem
                    book_name = book_name.replace('_', ' ')
                    
                    print(f"    📖 Importing {book_name}...", end=' ')
                    
                    try:
                        verses = self.parse_bible_text_file(txt_file, lang_code)
                        
                        if not verses:
                            print(f"⚠ No verses found")
                            continue
                        
                        language_id = self.get_language_id(lang_code)
                        testament_id = self.get_or_create_testament(book_name)
                        book_id = self.get_or_create_book(book_name, testament_id)
                        
                        verse_count = 0
                        for verse_data in verses:
                            chapter_id = self.get_or_create_chapter(book_id, verse_data['chapter'])
                            verse_id = self.get_or_create_verse(chapter_id, verse_data['verse'])
                            self.insert_verse_text(verse_id, language_id, verse_data['text'])
                            verse_count += 1
                            stats['total_verses'] += 1
                            stats['languages'][lang_code] += 1
                            stats['books'].add(book_name)
                        
                        print(f"✅ {verse_count} verses")
                        self.conn.commit()
                        
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        continue
    
    def verify_import(self):
        """Verify the import results"""
        print("\n" + "="*60)
        print("📊 VERIFYING IMPORT")
        print("="*60)
        
        self.cursor.execute("SELECT COUNT(*) FROM testaments")
        testament_count = self.cursor.fetchone()[0]
        print(f"✓ Testaments: {testament_count}")
        
        self.cursor.execute("SELECT COUNT(*) FROM books")
        book_count = self.cursor.fetchone()[0]
        print(f"✓ Books: {book_count}")
        
        self.cursor.execute("SELECT COUNT(*) FROM chapters")
        chapter_count = self.cursor.fetchone()[0]
        print(f"✓ Chapters: {chapter_count}")
        
        self.cursor.execute("SELECT COUNT(*) FROM verses")
        verse_count = self.cursor.fetchone()[0]
        print(f"✓ Verses: {verse_count}")
        
        self.cursor.execute("""
            SELECT l.code, COUNT(vt.id) 
            FROM verse_texts vt
            JOIN languages l ON vt.language_id = l.id
            GROUP BY l.id
        """)
        lang_counts = self.cursor.fetchall()
        print(f"\n✓ Verse Texts by Language:")
        for lang_code, count in lang_counts:
            lang_name = {'am': 'Amharic', 'en': 'English', 'or': 'Oromo'}.get(lang_code, lang_code)
            print(f"   {lang_name} ({lang_code}): {count}")
        
        print(f"\n📖 Sample Data:")
        self.cursor.execute("""
            SELECT b.name, c.chapter_number, v.verse_number, vt.text, l.code
            FROM verse_texts vt
            JOIN verses v ON vt.verse_id = v.id
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            JOIN languages l ON vt.language_id = l.id
            WHERE l.code = 'en'
            LIMIT 5
        """)
        
        samples = self.cursor.fetchall()
        for sample in samples:
            print(f"   {sample[0]} {sample[1]}:{sample[2]} ({sample[4]}) - {sample[3][:50]}...")
    
    def run(self):
        print("="*60)
        print("🚀 COMPLETE BIBLE DATABASE IMPORTER")
        print("="*60)
        
        try:
            self.connect()
            print(f"✓ Connected to database: {self.db_path}")
            
            # Check if languages table exists
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='languages'")
            if not self.cursor.fetchone():
                print("❌ Languages table not found. Please run 'python app/init_db.py' first.")
                return
            
            self.import_all_bibles()
            self.verify_import()
            
            print("\n" + "="*60)
            print("✅ IMPORT COMPLETE SUCCESSFULLY!")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error during import: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()


if __name__ == "__main__":
    importer = CompleteBibleImporter()
    importer.run()