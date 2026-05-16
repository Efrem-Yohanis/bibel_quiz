# app/database.py
# Import patch first for Python 3.14 compatibility
import sys
if sys.version_info >= (3, 14):
    from app.database_patch import *

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# SQLite database file
SQLALCHEMY_DATABASE_URL = "sqlite:///./bible_quiz.db"

# Create engine (SQLite specific configuration)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()