# app/database.py

# Import patch first for Python 3.14 compatibility
import sys
if sys.version_info >= (3, 14):
    from app.database_patch import *

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

# 1. Hardcoded Render Internal Database URL
DATABASE_URL = "postgresql://bibel_quiz_user:IBQceDb477BJ0i7DWL4MSIOy6hnkATEO@dpg-d84b0f58nd3s73ctqle0-a/bibel_quiz"

# 2. Fix for Render PostgreSQL URL (postgres:// → postgresql://) if modified later
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Fallback to SQLite for local development (Triggers only if you comment out or clear the URL above)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./bible_quiz.db"

# Create engine with proper config
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True  # Important for production (Render)
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()