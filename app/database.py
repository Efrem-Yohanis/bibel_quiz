# app/database.py
import sys
if sys.version_info >= (3, 14):
    from app.database_patch import *

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

# Force use of PostgreSQL on Render
# Check if running on Render
IS_RENDER = os.environ.get('RENDER') or os.environ.get('DATABASE_URL')

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('RENDER_DATABASE_URL')

# Convert postgres:// to postgresql:// for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# On Render, REQUIRE PostgreSQL
if IS_RENDER:
    if not DATABASE_URL:
        raise ValueError(
            "❌ DATABASE_URL environment variable is required on Render!\n"
            "   Please set DATABASE_URL in your Render environment variables."
        )
    
    if 'sqlite' in DATABASE_URL.lower():
        raise ValueError(
            "❌ SQLite is not allowed on Render!\n"
            "   Please set DATABASE_URL to your PostgreSQL connection string."
        )
    
    print("✅ Running on Render with PostgreSQL")
    print(f"   Database: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'PostgreSQL'}")
else:
    # Local development - can use SQLite or PostgreSQL
    if not DATABASE_URL:
        DATABASE_URL = 'sqlite:///./bible_quiz.db'
        print("⚠️  Using SQLite for local development")
    else:
        print("✅ Using database from DATABASE_URL")

# Create engine with PostgreSQL optimizations
if DATABASE_URL.startswith('sqlite'):
    # SQLite configuration (local only)
    engine = create_engine(
        DATABASE_URL,
        connect_args={'check_same_thread': False},
        echo=False
    )
else:
    # PostgreSQL configuration (Render)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,           # Verify connections before using
        pool_recycle=3600,            # Recycle connections every hour
        pool_size=10,                 # Maximum connections in pool
        max_overflow=20,              # Extra connections beyond pool_size
        pool_timeout=30,              # Timeout for getting connection from pool
        echo=False,                   # Set to True for SQL debugging
        connect_args={
            'connect_timeout': 10,    # Connection timeout in seconds
            'keepalives': 1,          # Enable TCP keepalives
            'keepalives_idle': 30,    # Seconds before sending keepalive
            'keepalives_interval': 10, # Seconds between keepalives
            'keepalives_count': 5      # Number of keepalives before timeout
        }
    )
    print("✅ PostgreSQL engine configured")

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class
Base = declarative_base()

# Dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test function
def test_connection():
    """Test database connection"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def init_db():
    """Create all tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables verified")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False