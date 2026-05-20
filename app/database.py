
import sys
if sys.version_info >= (3, 14):
    from app.database_patch import *

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

# Use external DB URL from environment variable when available.
# Render sets DATABASE_URL in the environment for managed PostgreSQL services.
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('RENDER_DATABASE_URL')

# If the Render PostgreSQL URL is provided as postgres://, SQLAlchemy prefers postgresql://.
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Local fallback for development when no external DB URL is set.
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///./bible_quiz.db'

# Create engine
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        DATABASE_URL,
        connect_args={'check_same_thread': False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

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