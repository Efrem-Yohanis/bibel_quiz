# admin_center_api/services/language_management_service.py
"""
Admin Language Management Service
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / 'app' / 'bible_quiz.db'

class LanguageManagementService:
    """Service for admin language management"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_all_languages(self) -> List[Dict]:
        """Get all languages"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, code, name, native_name, is_active, created_at
            FROM languages
            ORDER BY id
        """)
        
        languages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return languages
    
    def add_language(self, code: str, name: str, native_name: str) -> Dict:
        """Add a new language"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Check if language already exists
        cursor.execute("SELECT id FROM languages WHERE code = ?", (code,))
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'message': f'Language with code "{code}" already exists'}
        
        cursor.execute("""
            INSERT INTO languages (code, name, native_name, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
        """, (code, name, native_name, datetime.utcnow()))
        
        language_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'language_id': language_id, 'message': 'Language added successfully'}
    
    def update_language(self, language_id: int, code: str = None, name: str = None, 
                        native_name: str = None, is_active: bool = None) -> Dict:
        """Update language information"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if code:
            updates.append("code = ?")
            params.append(code)
        if name:
            updates.append("name = ?")
            params.append(name)
        if native_name:
            updates.append("native_name = ?")
            params.append(native_name)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        
        if not updates:
            conn.close()
            return {'success': False, 'message': 'No fields to update'}
        
        updates.append("created_at = created_at")
        params.append(language_id)
        
        query = f"UPDATE languages SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected > 0:
            return {'success': True, 'message': 'Language updated successfully'}
        return {'success': False, 'message': 'Language not found'}
    
    def delete_language(self, language_id: int) -> Dict:
        """Delete a language (only if no references exist)"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Check if language is used in verse_texts
        cursor.execute("SELECT COUNT(*) FROM verse_texts WHERE language_id = ?", (language_id,))
        verse_count = cursor.fetchone()[0]
        
        if verse_count > 0:
            conn.close()
            return {'success': False, 'message': f'Cannot delete: Language is used in {verse_count} verses'}
        
        # Check if language is used in question_texts
        cursor.execute("SELECT COUNT(*) FROM question_texts WHERE language_id = ?", (language_id,))
        question_count = cursor.fetchone()[0]
        
        if question_count > 0:
            conn.close()
            return {'success': False, 'message': f'Cannot delete: Language is used in {question_count} questions'}
        
        cursor.execute("DELETE FROM languages WHERE id = ?", (language_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected > 0:
            return {'success': True, 'message': 'Language deleted successfully'}
        return {'success': False, 'message': 'Language not found'}