# scripts/create_postgres_tables_only.py
"""
Create PostgreSQL tables only (no data migration)
Run: python scripts/create_postgres_tables_only.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL connection URL
POSTGRES_URL = "postgresql://bibel_quiz_user:IBQceDb477BJ0i7DWL4MSIOy6hnkATEO@dpg-d84b0f58nd3s73ctqle0-a.oregon-postgres.render.com/bibel_quiz"

# SQL to create all tables
CREATE_TABLES_SQL = """
-- Drop all tables if they exist (in correct order)
DROP TABLE IF EXISTS user_book_progress CASCADE;
DROP TABLE IF EXISTS quiz_answers CASCADE;
DROP TABLE IF EXISTS quiz_attempts CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS explanations CASCADE;
DROP TABLE IF EXISTS option_texts CASCADE;
DROP TABLE IF EXISTS options CASCADE;
DROP TABLE IF EXISTS question_texts CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS verse_texts CASCADE;
DROP TABLE IF EXISTS verses CASCADE;
DROP TABLE IF EXISTS chapters CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS testaments CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS levels CASCADE;
DROP TABLE IF EXISTS languages CASCADE;

-- 1. Languages table
CREATE TABLE languages (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    native_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Levels table
CREATE TABLE levels (
    id SERIAL PRIMARY KEY,
    level_number INTEGER UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    color VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Testaments table
CREATE TABLE testaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

-- 4. Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    total_quizzes_taken INTEGER DEFAULT 0,
    total_correct_answers INTEGER DEFAULT 0,
    total_questions_answered INTEGER DEFAULT 0,
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP,
    preferred_language_id INTEGER REFERENCES languages(id)
);

-- 5. Books table
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    testament_id INTEGER REFERENCES testaments(id)
);

-- 6. Chapters table
CREATE TABLE chapters (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(id),
    chapter_number INTEGER NOT NULL
);

-- 7. Verses table
CREATE TABLE verses (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER REFERENCES chapters(id),
    verse_number INTEGER NOT NULL
);

-- 8. Verse texts table
CREATE TABLE verse_texts (
    id SERIAL PRIMARY KEY,
    verse_id INTEGER REFERENCES verses(id),
    language_id INTEGER REFERENCES languages(id),
    text TEXT NOT NULL
);

-- 9. Questions table
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(id),
    chapter_id INTEGER REFERENCES chapters(id),
    level_id INTEGER REFERENCES levels(id),
    correct_option VARCHAR(1) NOT NULL,
    verse_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Question texts table
CREATE TABLE question_texts (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    language_id INTEGER REFERENCES languages(id),
    text TEXT NOT NULL
);

-- 11. Options table
CREATE TABLE options (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    label VARCHAR(1) NOT NULL
);

-- 12. Option texts table
CREATE TABLE option_texts (
    id SERIAL PRIMARY KEY,
    option_id INTEGER REFERENCES options(id),
    language_id INTEGER REFERENCES languages(id),
    text TEXT NOT NULL
);

-- 13. Explanations table
CREATE TABLE explanations (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    language_id INTEGER REFERENCES languages(id),
    text TEXT NOT NULL
);

-- 14. User sessions table
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. Quiz attempts table
CREATE TABLE quiz_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    book_id INTEGER REFERENCES books(id),
    level_id INTEGER REFERENCES levels(id),
    language_id INTEGER REFERENCES languages(id),
    total_questions INTEGER DEFAULT 0,
    answered_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    score_percentage REAL DEFAULT 0,
    status VARCHAR(20) DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    resume_data TEXT
);

-- 16. Quiz answers table
CREATE TABLE quiz_answers (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER REFERENCES quiz_attempts(id),
    question_id INTEGER REFERENCES questions(id),
    selected_option VARCHAR(1),
    is_correct BOOLEAN,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_info TEXT
);

-- 17. User book progress table
CREATE TABLE user_book_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    book_id INTEGER REFERENCES books(id),
    current_chapter INTEGER DEFAULT 1,
    current_verse INTEGER DEFAULT 1,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    questions_answered INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, book_id)
);

-- Insert initial data
INSERT INTO languages (id, code, name, native_name, is_active) VALUES
(1, 'en', 'English', 'English', TRUE),
(2, 'am', 'Amharic', 'አማርኛ', TRUE),
(3, 'or', 'Oromo', 'Afaan Oromoo', TRUE),
(4, 'ti', 'Tigrinya', 'ትግርኛ', TRUE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO levels (id, level_number, name, description, icon, color) VALUES
(1, 1, 'Easy', 'Basic questions directly from the text', '🌟', '#4CAF50'),
(2, 2, 'Medium', 'Questions about meaning and context', '⭐', '#FF9800'),
(3, 3, 'Hard', 'In-depth questions requiring deep understanding', '🏆', '#F44336')
ON CONFLICT (id) DO NOTHING;

INSERT INTO testaments (id, name) VALUES
(1, 'Old'),
(2, 'New')
ON CONFLICT (id) DO NOTHING;

-- Reset sequences
SELECT setval('languages_id_seq', (SELECT COALESCE(MAX(id), 0) FROM languages));
SELECT setval('levels_id_seq', (SELECT COALESCE(MAX(id), 0) FROM levels));
SELECT setval('testaments_id_seq', (SELECT COALESCE(MAX(id), 0) FROM testaments));
"""

def create_tables():
    """Create all tables in PostgreSQL"""
    print("="*60)
    print("🐘 CREATING POSTGRESQL TABLES")
    print("="*60)
    
    try:
        # Connect to PostgreSQL
        print("\n📡 Connecting to PostgreSQL...")
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        
        # Execute table creation
        print("\n📦 Creating tables...")
        cursor.execute(CREATE_TABLES_SQL)
        conn.commit()
        print("✅ Tables created successfully!")
        
        # Verify tables
        print("\n📊 Verifying tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"\n✅ {len(tables)} tables created:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   📋 {table[0]}: {count} rows")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ POSTGRESQL TABLES CREATION COMPLETE!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()