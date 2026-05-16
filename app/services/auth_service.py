# app/services/auth_service.py
"""
Authentication Service for Bible Quiz Application
Handles user registration, login, password management, and session handling
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import User, UserSession
from schemas.schemas import UserCreate, UserLogin, UserResponse, TokenResponse

class AuthService:
    """Authentication service for user management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Password Utilities ====================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using SHA-256 with salt
        In production, use bcrypt or argon2 instead
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """
        Verify password against stored hash
        """
        try:
            salt, hash_value = stored_hash.split(':')
            computed_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
            return computed_hash == hash_value
        except:
            return False
    
    @staticmethod
    def generate_token() -> str:
        """
        Generate a secure session token
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength
        Returns (is_valid, error_message)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        if len(password) > 100:
            return False, "Password must be less than 100 characters"
        
        # Optional: Add more strength checks
        # if not re.search(r'[A-Z]', password):
        #     return False, "Password must contain at least one uppercase letter"
        # if not re.search(r'[0-9]', password):
        #     return False, "Password must contain at least one number"
        
        return True, None
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, Optional[str]]:
        """
        Validate username format
        """
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 50:
            return False, "Username must be less than 50 characters"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        return True, None
    
    # ==================== User Management ====================
    
    def register_user(self, user_data: UserCreate) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Register a new user
        Returns (user_response, error_message)
        """
        # Validate username
        is_valid, error = self.validate_username(user_data.username)
        if not is_valid:
            return None, error
        
        # Check if username already exists
        existing_user = self.db.query(User).filter(
            User.username == user_data.username
        ).first()
        if existing_user:
            return None, "Username already exists"
        
        # Validate email if provided
        if user_data.email:
            if not self.validate_email(user_data.email):
                return None, "Invalid email format"
            
            # Check if email already exists
            existing_email = self.db.query(User).filter(
                User.email == user_data.email
            ).first()
            if existing_email:
                return None, "Email already registered"
        
        # Validate password strength
        is_valid, error = self.validate_password_strength(user_data.password)
        if not is_valid:
            return None, error
        
        # Hash password
        hashed_password = self.hash_password(user_data.password)
        
        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True,
            total_quizzes_taken=0,
            total_correct_answers=0,
            total_questions_answered=0
        )
        
        try:
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            # Create user response (without sensitive data)
            user_response = UserResponse(
                id=new_user.id,
                username=new_user.username,
                email=new_user.email,
                created_at=new_user.created_at,
                is_active=new_user.is_active,
                total_quizzes_taken=new_user.total_quizzes_taken,
                total_correct_answers=new_user.total_correct_answers,
                total_questions_answered=new_user.total_questions_answered
            )
            
            return user_response, None
            
        except Exception as e:
            self.db.rollback()
            return None, f"Registration failed: {str(e)}"
    
    def login_user(self, login_data: UserLogin) -> Tuple[Optional[TokenResponse], Optional[str]]:
        """
        Authenticate user and create session
        Returns (token_response, error_message)
        """
        # Find user by username or email
        user = self.db.query(User).filter(
            (User.username == login_data.username_or_email) |
            (User.email == login_data.username_or_email)
        ).first()
        
        if not user:
            return None, "Invalid username/email or password"
        
        # Check if user is active
        if not user.is_active:
            return None, "Account is deactivated. Please contact support."
        
        # Verify password
        if not self.verify_password(login_data.password, user.password_hash):
            return None, "Invalid username/email or password"
        
        # Generate session token
        token = self.generate_token()
        
        # Set expiration (30 days from now)
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        # Create new session
        new_session = UserSession(
            user_id=user.id,
            token=token,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True,
            ip_address=login_data.ip_address if hasattr(login_data, 'ip_address') else None,
            user_agent=login_data.user_agent if hasattr(login_data, 'user_agent') else None
        )
        
        try:
            # Deactivate any existing sessions (optional - for single session per user)
            # self.db.query(UserSession).filter(
            #     UserSession.user_id == user.id,
            #     UserSession.is_active == True
            # ).update({"is_active": False})
            
            self.db.add(new_session)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Update user statistics (optional)
            self.update_user_stats(user.id)
            
            token_response = TokenResponse(
                access_token=token,
                token_type="bearer",
                expires_at=expires_at,
                user_id=user.id,
                username=user.username
            )
            
            return token_response, None
            
        except Exception as e:
            self.db.rollback()
            return None, f"Login failed: {str(e)}"
    
    def logout_user(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Logout user by deactivating session
        Returns (success, error_message)
        """
        session = self.db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            return False, "Invalid or expired session"
        
        try:
            session.is_active = False
            self.db.commit()
            return True, None
        except Exception as e:
            self.db.rollback()
            return False, f"Logout failed: {str(e)}"
    
    def logout_all_sessions(self, user_id: int, current_token: str) -> Tuple[bool, Optional[str]]:
        """
        Logout from all devices except current session
        """
        try:
            self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.token != current_token,
                UserSession.is_active == True
            ).update({"is_active": False})
            
            self.db.commit()
            return True, None
        except Exception as e:
            self.db.rollback()
            return False, f"Failed to logout other sessions: {str(e)}"
    
    # ==================== Session Management ====================
    
    def validate_session(self, token: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Validate session token and return user if valid
        Returns (user, error_message)
        """
        session = self.db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            return None, "Invalid session"
        
        # Check if session has expired
        if session.expires_at < datetime.utcnow():
            session.is_active = False
            self.db.commit()
            return None, "Session has expired. Please login again."
        
        # Get user
        user = self.db.query(User).filter(User.id == session.user_id).first()
        
        if not user or not user.is_active:
            return None, "User not found or deactivated"
        
        return user, None
    
    def refresh_session(self, token: str) -> Tuple[Optional[TokenResponse], Optional[str]]:
        """
        Refresh session token (extend expiration)
        """
        session = self.db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            return None, "Invalid session"
        
        # Check if session has expired
        if session.expires_at < datetime.utcnow():
            session.is_active = False
            self.db.commit()
            return None, "Session has expired. Please login again."
        
        try:
            # Extend session by 30 days
            session.expires_at = datetime.utcnow() + timedelta(days=30)
            session.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Get user
            user = self.db.query(User).filter(User.id == session.user_id).first()
            
            token_response = TokenResponse(
                access_token=session.token,
                token_type="bearer",
                expires_at=session.expires_at,
                user_id=user.id,
                username=user.username
            )
            
            return token_response, None
            
        except Exception as e:
            self.db.rollback()
            return None, f"Session refresh failed: {str(e)}"
    
    # ==================== Password Management ====================
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Change user password
        Returns (success, error_message)
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False, "User not found"
        
        # Verify old password
        if not self.verify_password(old_password, user.password_hash):
            return False, "Incorrect current password"
        
        # Validate new password
        is_valid, error = self.validate_password_strength(new_password)
        if not is_valid:
            return False, error
        
        # Hash new password
        new_hash = self.hash_password(new_password)
        
        try:
            user.password_hash = new_hash
            user.updated_at = datetime.utcnow()
            
            # Optional: Invalidate all sessions after password change
            # self.db.query(UserSession).filter(
            #     UserSession.user_id == user_id,
            #     UserSession.is_active == True
            # ).update({"is_active": False})
            
            self.db.commit()
            return True, None
            
        except Exception as e:
            self.db.rollback()
            return False, f"Password change failed: {str(e)}"
    
    def reset_password_request(self, email: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Request password reset (generate reset token)
        Returns (success, reset_token, error_message)
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal that email doesn't exist for security
            return True, None, None
        
        # Generate reset token
        reset_token = self.generate_token()
        
        # Store reset token with expiration
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
        user.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            # In production, send email with reset link
            # For now, return the token
            return True, reset_token, None
        except Exception as e:
            self.db.rollback()
            return False, None, f"Reset request failed: {str(e)}"
    
    def reset_password(self, reset_token: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Reset password using reset token
        Returns (success, error_message)
        """
        user = self.db.query(User).filter(
            User.reset_token == reset_token,
            User.reset_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            return False, "Invalid or expired reset token"
        
        # Validate new password
        is_valid, error = self.validate_password_strength(new_password)
        if not is_valid:
            return False, error
        
        # Hash new password
        new_hash = self.hash_password(new_password)
        
        try:
            user.password_hash = new_hash
            user.reset_token = None
            user.reset_token_expires = None
            user.updated_at = datetime.utcnow()
            
            # Invalidate all sessions after password reset
            self.db.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).update({"is_active": False})
            
            self.db.commit()
            return True, None
            
        except Exception as e:
            self.db.rollback()
            return False, f"Password reset failed: {str(e)}"
    
    # ==================== User Profile Management ====================
    
    def get_user_profile(self, user_id: int) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Get user profile by ID
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None, "User not found"
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active,
            total_quizzes_taken=user.total_quizzes_taken,
            total_correct_answers=user.total_correct_answers,
            total_questions_answered=user.total_questions_answered
        )
        
        return user_response, None
    
    def update_user_profile(self, user_id: int, username: Optional[str] = None, 
                           email: Optional[str] = None) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Update user profile information
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None, "User not found"
        
        # Update username if provided
        if username:
            is_valid, error = self.validate_username(username)
            if not is_valid:
                return None, error
            
            # Check if username is taken
            existing = self.db.query(User).filter(
                User.username == username,
                User.id != user_id
            ).first()
            if existing:
                return None, "Username already taken"
            
            user.username = username
        
        # Update email if provided
        if email:
            if not self.validate_email(email):
                return None, "Invalid email format"
            
            # Check if email is taken
            existing = self.db.query(User).filter(
                User.email == email,
                User.id != user_id
            ).first()
            if existing:
                return None, "Email already registered"
            
            user.email = email
        
        user.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(user)
            
            user_response = UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                created_at=user.created_at,
                is_active=user.is_active,
                total_quizzes_taken=user.total_quizzes_taken,
                total_correct_answers=user.total_correct_answers,
                total_questions_answered=user.total_questions_answered
            )
            
            return user_response, None
            
        except Exception as e:
            self.db.rollback()
            return None, f"Profile update failed: {str(e)}"
    
    def deactivate_account(self, user_id: int, password: str) -> Tuple[bool, Optional[str]]:
        """
        Deactivate user account
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False, "User not found"
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            return False, "Incorrect password"
        
        try:
            # Deactivate user
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            # Deactivate all sessions
            self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).update({"is_active": False})
            
            self.db.commit()
            return True, None
            
        except Exception as e:
            self.db.rollback()
            return False, f"Account deactivation failed: {str(e)}"
    
    # ==================== Statistics and Analytics ====================
    
    def update_user_stats(self, user_id: int) -> None:
        """
        Update user statistics based on quiz attempts
        """
        from models import QuizAttempt, QuizAnswer
        
        # Get all quiz attempts for user
        attempts = self.db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id
        ).all()
        
        total_quizzes = len(attempts)
        total_answers = 0
        correct_answers = 0
        
        for attempt in attempts:
            answers = self.db.query(QuizAnswer).filter(
                QuizAnswer.attempt_id == attempt.id
            ).all()
            
            total_answers += len(answers)
            correct_answers += sum(1 for a in answers if a.is_correct)
        
        # Update user stats
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.total_quizzes_taken = total_quizzes
            user.total_questions_answered = total_answers
            user.total_correct_answers = correct_answers
            
            try:
                self.db.commit()
            except:
                self.db.rollback()
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get detailed user statistics
        """
        from models import QuizAttempt
        
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {}
        
        # Calculate accuracy
        accuracy = 0
        if user.total_questions_answered > 0:
            accuracy = (user.total_correct_answers / user.total_questions_answered) * 100
        
        # Get recent attempts
        recent_attempts = self.db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id
        ).order_by(QuizAttempt.date.desc()).limit(10).all()
        
        return {
            'total_quizzes_taken': user.total_quizzes_taken,
            'total_questions_answered': user.total_questions_answered,
            'total_correct_answers': user.total_correct_answers,
            'accuracy_percentage': round(accuracy, 2),
            'member_since': user.created_at,
            'last_login': user.last_login,
            'recent_attempts': [
                {
                    'date': attempt.date,
                    'score': attempt.score,
                    'total_questions': attempt.total_questions
                }
                for attempt in recent_attempts
            ]
        }