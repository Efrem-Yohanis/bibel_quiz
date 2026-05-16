# app/services/auth_service_simple.py
"""
Simple Auth Service without SQLAlchemy for Python 3.14 compatibility
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

DB_PATH = Path(__file__).parent.parent / 'bible_quiz.db'

class AuthService:
    """Simple authentication service using SQLite directly"""
    
    def __init__(self, db=None):
        self.db_path = DB_PATH
        if db:
            self.db = db
        else:
            self.db = None
    
    def get_db(self):
        """Get database connection"""
        if self.db:
            return self.db
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify password"""
        try:
            salt, hash_value = stored_hash.split(':')
            computed_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
            return computed_hash == hash_value
        except:
            return False
    
    def register_user(self, user_data) -> Tuple[Optional[Any], Optional[str]]:
        """Register a new user"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # Check if username exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (user_data.username,))
            if cursor.fetchone():
                conn.close()
                return None, "Username already exists"
            
            # Check if email exists
            if user_data.email:
                cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
                if cursor.fetchone():
                    conn.close()
                    return None, "Email already registered"
            
            # Hash password and create user
            password_hash = self.hash_password(user_data.password)
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_data.username, user_data.email, password_hash, 
                  datetime.utcnow(), datetime.utcnow()))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Create a simple user object
            class User:
                def __init__(self, id, username, email, created_at):
                    self.id = id
                    self.username = username
                    self.email = email
                    self.created_at = created_at
                    self.total_quizzes_taken = 0
                    self.total_correct_answers = 0
                    self.total_questions_answered = 0
            
            user = User(user_id, user_data.username, user_data.email, datetime.utcnow())
            conn.close()
            return user, None
            
        except Exception as e:
            conn.close()
            return None, f"Registration failed: {str(e)}"
    
    def login_user(self, login_data) -> Tuple[Optional[Any], Optional[str]]:
        """Login user and create session"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # Find user by username or email
            cursor.execute("""
                SELECT id, username, email, password_hash, is_active 
                FROM users 
                WHERE username = ? OR email = ?
            """, (login_data.username_or_email, login_data.username_or_email))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return None, "Invalid username/email or password"
            
            if not user['is_active']:
                conn.close()
                return None, "Account is deactivated"
            
            if not self.verify_password(login_data.password, user['password_hash']):
                conn.close()
                return None, "Invalid username/email or password"
            
            # Generate token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Store session
            cursor.execute("""
                INSERT INTO user_sessions (user_id, token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            """, (user['id'], token, expires_at, 
                  getattr(login_data, 'ip_address', None),
                  getattr(login_data, 'user_agent', None)))
            
            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = ?, updated_at = ?
                WHERE id = ?
            """, (datetime.utcnow(), datetime.utcnow(), user['id']))
            
            conn.commit()
            conn.close()
            
            # Create token response object
            class TokenResponse:
                def __init__(self, user_id, username, expires_at):
                    self.user_id = user_id
                    self.username = username
                    self.expires_at = expires_at
            
            token_response = TokenResponse(user['id'], user['username'], expires_at)
            return token_response, None
            
        except Exception as e:
            conn.close()
            return None, f"Login failed: {str(e)}"
    
    def logout_user(self, token: str) -> Tuple[bool, Optional[str]]:
        """Logout user by deactivating session"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE user_sessions SET is_active = 0 WHERE token = ?", (token,))
            conn.commit()
            conn.close()
            return True, None
        except Exception as e:
            conn.close()
            return False, f"Logout failed: {str(e)}"
    
    def get_user_profile(self, user_id: int) -> Tuple[Optional[Any], Optional[str]]:
        """Get user profile by ID"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, created_at, total_quizzes_taken,
                   total_correct_answers, total_questions_answered
            FROM users WHERE id = ? AND is_active = 1
        """, (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return None, "User not found"
        
        class User:
            def __init__(self, data):
                self.id = data['id']
                self.username = data['username']
                self.email = data['email']
                self.created_at = data['created_at']
                self.total_quizzes_taken = data['total_quizzes_taken'] or 0
                self.total_correct_answers = data['total_correct_answers'] or 0
                self.total_questions_answered = data['total_questions_answered'] or 0
        
        return User(user), None
    
    def update_user_profile(self, user_id: int, username: str = None, email: str = None) -> Tuple[Optional[Any], Optional[str]]:
        """Update user profile"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if username:
            cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
            if cursor.fetchone():
                conn.close()
                return None, "Username already taken"
            updates.append("username = ?")
            params.append(username)
        
        if email:
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
            if cursor.fetchone():
                conn.close()
                return None, "Email already registered"
            updates.append("email = ?")
            params.append(email)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow())
            params.append(user_id)
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        # Get updated user
        cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        class User:
            def __init__(self, data):
                self.id = data['id']
                self.username = data['username']
                self.email = data['email']
        
        return User(user), None