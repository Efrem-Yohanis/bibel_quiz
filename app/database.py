# app/database.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

# Force PostgreSQL on Render
IS_RENDER = os.environ.get('RENDER') == 'true'

# Get database URL
DATABASE_URL = os.environ.get('DATABASE_URL')

if IS_RENDER:
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is required on Render")
    
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    if '?sslmode=require' in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace('?sslmode=require', '')
    
    print("✅ PostgreSQL configured")
else:
    if not DATABASE_URL:
        DATABASE_URL = 'sqlite:///bible_quiz.db'
        print("⚠️ Using SQLite for local development")

# Create engine
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Add query property to Base for compatibility
class QueryMixin:
    @classmethod
    def query(cls):
        return SessionLocal().query(cls)

Base.query = QueryMixin.query

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables verified")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False