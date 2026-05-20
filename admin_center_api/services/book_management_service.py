# admin_center_api/services/book_management_service.py
"""
Admin Book Management Service
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / 'app' / 'bible_quiz.db'

class BookManagementService:
    """Service for admin book management"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_all_books(self, testament: str = None) -> List[Dict]:
        """Get all books, optionally filtered by testament"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        if testament:
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
            """, (testament,))
        else:
            cursor.execute("""
                SELECT b.id, b.name, t.name as testament,
                       COUNT(DISTINCT c.id) as chapters,
                       COUNT(DISTINCT v.id) as verses
                FROM books b
                JOIN testaments t ON b.testament_id = t.id
                LEFT JOIN chapters c ON c.book_id = b.id
                LEFT JOIN verses v ON v.chapter_id = c.id
                GROUP BY b.id
                ORDER BY b.id
            """)
        
        books = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return books
    
    def get_book_by_id(self, book_id: int) -> Optional[Dict]:
        """Get book by ID"""
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
            WHERE b.id = ?
            GROUP BY b.id
        """, (book_id,))
        
        book = cursor.fetchone()
        conn.close()
        return dict(book) if book else None
    
    def add_book(self, name: str, testament: str) -> Dict:
        """Add a new book"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get testament ID
        cursor.execute("SELECT id FROM testaments WHERE name = ?", (testament,))
        testament_row = cursor.fetchone()
        
        if not testament_row:
            conn.close()
            return {'success': False, 'message': f'Testament "{testament}" not found'}
        
        testament_id = testament_row['id']
        
        # Check if book already exists
        cursor.execute("SELECT id FROM books WHERE name = ?", (name,))
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'message': f'Book "{name}" already exists'}
        
        cursor.execute("""
            INSERT INTO books (name, testament_id)
            VALUES (?, ?)
        """, (name, testament_id))
        
        book_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'book_id': book_id, 'message': 'Book added successfully'}
    
    def update_book(self, book_id: int, name: str = None, testament: str = None) -> Dict:
        """Update book information"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        
        if testament:
            cursor.execute("SELECT id FROM testaments WHERE name = ?", (testament,))
            testament_row = cursor.fetchone()
            if not testament_row:
                conn.close()
                return {'success': False, 'message': f'Testament "{testament}" not found'}
            updates.append("testament_id = ?")
            params.append(testament_row['id'])
        
        if not updates:
            conn.close()
            return {'success': False, 'message': 'No fields to update'}
        
        params.append(book_id)
        query = f"UPDATE books SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected > 0:
            return {'success': True, 'message': 'Book updated successfully'}
        return {'success': False, 'message': 'Book not found'}
    
    def delete_book(self, book_id: int) -> Dict:
        """Delete a book (cascade will handle related records)"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Check if book has questions
        cursor.execute("SELECT COUNT(*) FROM questions WHERE book_id = ?", (book_id,))
        question_count = cursor.fetchone()[0]
        
        if question_count > 0:
            conn.close()
            return {'success': False, 'message': f'Cannot delete: Book has {question_count} questions'}
        
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected > 0:
            return {'success': True, 'message': 'Book deleted successfully'}
        return {'success': False, 'message': 'Book not found'}