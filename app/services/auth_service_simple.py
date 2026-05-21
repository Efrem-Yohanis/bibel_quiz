# app/services/auth_service_simple.py - PostgreSQL version
"""
Simple Auth Service using PostgreSQL via SQLAlchemy
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from app.database import get_db
from app.models import User, UserSession

class AuthService:
    """Authentication service using PostgreSQL via SQLAlchemy"""
    
    def __init__(self, db=None):
        self.db = db
    
    def _get_db(self):
        """Get database session"""
        if self.db:
            return self.db
        return next(get_db())
    
    def register_user(self, user_data) -> Tuple[Optional[Any], Optional[str]]:
        """Register a new user"""
        db = self._get_db()
        
        try:
            # Check if username exists
            existing_user = db.query(User).filter(User.username == user_data.username).first()
            if existing_user:
                return None, "Username already exists"
            
            # Check if email exists
            if user_data.email:
                existing_email = db.query(User).filter(User.email == user_data.email).first()
                if existing_email:
                    return None, "Email already registered"
            
            # Create new user
            new_user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=generate_password_hash(user_data.password),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return new_user, None
            
        except Exception as e:
            db.rollback()
            return None, f"Registration failed: {str(e)}"
    
    def login_user(self, login_data) -> Tuple[Optional[Any], Optional[str]]:
        """Login user and create session"""
        db = self._get_db()
        
        try:
            # Find user by username or email
            user = db.query(User).filter(
                (User.username == login_data.username_or_email) | 
                (User.email == login_data.username_or_email)
            ).first()
            
            if not user:
                return None, "Invalid username/email or password"
            
            if not user.is_active:
                return None, "Account is deactivated"
            
            if not check_password_hash(user.password_hash, login_data.password):
                return None, "Invalid username/email or password"
            
            # Generate session token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Create session
            session = UserSession(
                user_id=user.id,
                token=token,
                expires_at=expires_at,
                ip_address=getattr(login_data, 'ip_address', None),
                user_agent=getattr(login_data, 'user_agent', None),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Update last login
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            db.add(session)
            db.commit()
            
            # Create token response object
            class TokenResponse:
                def __init__(self, user_id, username, expires_at, is_admin):
                    self.user_id = user_id
                    self.username = username
                    self.expires_at = expires_at
                    self.is_admin = bool(is_admin)
            
            token_response = TokenResponse(user.id, user.username, expires_at, user.is_admin)
            return token_response, None
            
        except Exception as e:
            db.rollback()
            return None, f"Login failed: {str(e)}"
    
    def get_user_by_google_id(self, google_id: str):
        """Find a user by their Google account ID."""
        db = self._get_db()
        return db.query(User).filter(User.google_id == google_id).first()
    
    def get_user_by_email(self, email: str):
        """Find a user by email address."""
        db = self._get_db()
        return db.query(User).filter(User.email == email).first()
    
    def link_google_account(self, user_id: int, google_id: str, provider: str = 'google') -> Tuple[bool, Optional[str]]:
        """Link an existing user account to a Google account."""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.google_id = google_id
                user.auth_provider = provider
                user.updated_at = datetime.utcnow()
                db.commit()
                return True, None
            return False, "User not found"
        except Exception as e:
            db.rollback()
            return False, f"Linking Google account failed: {str(e)}"
    
    def create_google_user(self, username: str, email: str, google_id: str, provider: str = 'google') -> Tuple[Optional[Any], Optional[str], Optional[str]]:
        """Create a new user account for a Google-authenticated user."""
        db = self._get_db()
        try:
            if email:
                existing = db.query(User).filter(User.email == email).first()
                if existing:
                    return None, None, "Email already registered"
            
            temp_password = secrets.token_urlsafe(12)
            password_hash = generate_password_hash(temp_password)
            
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                google_id=google_id,
                auth_provider=provider,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return new_user, temp_password, None
        except Exception as e:
            db.rollback()
            return None, None, f"Google user creation failed: {str(e)}"
    
    def set_password_reset_token(self, email: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate and store a password reset token for a user."""
        db = self._get_db()
        reset_token = secrets.token_urlsafe(24)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None, "User with that email does not exist"
            
            user.reset_token = reset_token
            user.reset_token_expires = expires_at
            user.updated_at = datetime.utcnow()
            db.commit()
            return reset_token, None
        except Exception as e:
            db.rollback()
            return None, f"Password reset token generation failed: {str(e)}"
    
    def reset_password(self, reset_token: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """Reset a user's password using a valid reset token."""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.reset_token == reset_token).first()
            
            if not user:
                return False, "Invalid or expired reset token"
            
            if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
                return False, "Reset token has expired"
            
            user.password_hash = generate_password_hash(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            user.updated_at = datetime.utcnow()
            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            return False, f"Password reset failed: {str(e)}"
    
    def logout_user(self, token: str) -> Tuple[bool, Optional[str]]:
        """Logout user by deactivating session"""
        db = self._get_db()
        try:
            session = db.query(UserSession).filter(UserSession.token == token).first()
            if session:
                session.is_active = False
                session.updated_at = datetime.utcnow()
                db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            return False, f"Logout failed: {str(e)}"
    
    def get_user_profile(self, user_id: int):
        """Get user profile by ID"""
        db = self._get_db()
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        
        if not user:
            return None, "User not found"
        
        return user, None
    
    def update_user_profile(self, user_id: int, username: str = None, email: str = None):
        """Update user profile"""
        db = self._get_db()
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None, "User not found"
            
            if username:
                # Check if username is taken
                existing = db.query(User).filter(User.username == username, User.id != user_id).first()
                if existing:
                    return None, "Username already taken"
                user.username = username
            
            if email:
                # Check if email is taken
                existing = db.query(User).filter(User.email == email, User.id != user_id).first()
                if existing:
                    return None, "Email already registered"
                user.email = email
            
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            return user, None
        except Exception as e:
            db.rollback()
            return None, f"Update failed: {str(e)}"