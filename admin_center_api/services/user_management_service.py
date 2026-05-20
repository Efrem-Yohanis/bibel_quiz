# admin_center_api/services/user_management_service.py
"""
Admin User Management Service
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / 'app' / 'bible_quiz.db'

class UserManagementService:
    """Service for admin user management"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all registered users"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, created_at, last_login, is_active,
                   total_quizzes_taken, total_correct_answers, total_questions_answered, is_admin
            FROM users
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, created_at, last_login, is_active,
                   total_quizzes_taken, total_correct_answers, total_questions_answered, is_admin
            FROM users WHERE id = ?
        """, (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_user_quiz_progress(self, user_id: int) -> Dict:
        """Get user's quiz progress"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get all quiz attempts
        cursor.execute("""
            SELECT qa.id, b.name as book_name, l.name as level_name,
                   qa.total_questions, qa.correct_answers, qa.score_percentage,
                   qa.status, qa.started_at, qa.completed_at
            FROM quiz_attempts qa
            JOIN books b ON qa.book_id = b.id
            JOIN levels l ON qa.level_id = l.id
            WHERE qa.user_id = ?
            ORDER BY qa.started_at DESC
        """, (user_id,))
        
        attempts = [dict(row) for row in cursor.fetchall()]
        
        # Get book progress
        cursor.execute("""
            SELECT b.name as book_name, ubp.current_chapter, ubp.current_verse,
                   ubp.questions_answered, ubp.correct_answers, ubp.completed,
                   ubp.last_activity
            FROM user_book_progress ubp
            JOIN books b ON ubp.book_id = b.id
            WHERE ubp.user_id = ?
            ORDER BY b.name
        """, (user_id,))
        
        book_progress = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'quiz_attempts': attempts,
            'book_progress': book_progress,
            'total_quizzes': len(attempts),
            'total_books_progress': len(book_progress)
        }
    
    def toggle_user_status(self, user_id: int, is_active: bool) -> bool:
        """Activate or deactivate user"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET is_active = ?, updated_at = ?
            WHERE id = ?
        """, (1 if is_active else 0, datetime.utcnow(), user_id))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        return affected > 0

    def set_user_admin_status(self, user_id: int, is_admin: bool) -> bool:
        """Promote or demote a user to/from admin"""
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET is_admin = ?, updated_at = ?
            WHERE id = ?
        """, (1 if is_admin else 0, datetime.utcnow(), user_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_user_stats_summary(self) -> Dict:
        """Get summary statistics for all users"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                SUM(total_quizzes_taken) as total_quizzes,
                SUM(total_questions_answered) as total_questions,
                SUM(total_correct_answers) as total_correct,
                AVG(total_quizzes_taken) as avg_quizzes_per_user
            FROM users
        """)
        
        stats = cursor.fetchone()
        conn.close()
        
        return dict(stats) if stats else {}