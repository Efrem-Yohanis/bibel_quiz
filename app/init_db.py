# app/init_db.py
import sqlite3
import os
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'bible_quiz.db'

def init_database():
    """Create all database tables"""
    try:
        print("🔄 Creating database tables...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Languages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                native_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Levels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level_number INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                icon TEXT,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Testaments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS testaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        
        # 4. Books table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                testament_id INTEGER,
                FOREIGN KEY (testament_id) REFERENCES testaments (id)
            )
        """)
        
        # 5. Chapters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                chapter_number INTEGER NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        """)
        
        # 6. Verses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id INTEGER,
                verse_number INTEGER NOT NULL,
                FOREIGN KEY (chapter_id) REFERENCES chapters (id)
            )
        """)
        
        # 7. Verse Texts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verse_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verse_id INTEGER,
                language_id INTEGER,
                text TEXT NOT NULL,
                FOREIGN KEY (verse_id) REFERENCES verses (id),
                FOREIGN KEY (language_id) REFERENCES languages (id)
            )
        """)
        
        # 8. Questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                chapter_id INTEGER,
                level_id INTEGER,
                correct_option TEXT NOT NULL,
                verse_reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books (id),
                FOREIGN KEY (chapter_id) REFERENCES chapters (id),
                FOREIGN KEY (level_id) REFERENCES levels (id)
            )
        """)
        
        # 9. Question Texts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                language_id INTEGER,
                text TEXT NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions (id),
                FOREIGN KEY (language_id) REFERENCES languages (id)
            )
        """)
        
        # 10. Options table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                label TEXT NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
        """)
        
        # 11. Option Texts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS option_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                option_id INTEGER,
                language_id INTEGER,
                text TEXT NOT NULL,
                FOREIGN KEY (option_id) REFERENCES options (id),
                FOREIGN KEY (language_id) REFERENCES languages (id)
            )
        """)
        
        # 12. Explanations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS explanations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                language_id INTEGER,
                text TEXT NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions (id),
                FOREIGN KEY (language_id) REFERENCES languages (id)
            )
        """)
        
        # 13. Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                google_id TEXT,
                auth_provider TEXT,
                total_quizzes_taken INTEGER DEFAULT 0,
                total_correct_answers INTEGER DEFAULT 0,
                total_questions_answered INTEGER DEFAULT 0,
                reset_token TEXT,
                reset_token_expires TIMESTAMP,
                preferred_language_id INTEGER,
                FOREIGN KEY (preferred_language_id) REFERENCES languages (id)
            )
        """)
        
        # Add invisible admin and Google auth columns to existing DB if missing
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        if 'is_admin' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        if 'google_id' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        if 'auth_provider' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)")
        # 14. User Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                ip_address TEXT,
                user_agent TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # 15. Quiz Attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                book_id INTEGER,
                level_id INTEGER,
                language_id INTEGER,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                score_percentage REAL DEFAULT 0,
                status TEXT DEFAULT 'in_progress',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                resume_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (book_id) REFERENCES books (id),
                FOREIGN KEY (level_id) REFERENCES levels (id),
                FOREIGN KEY (language_id) REFERENCES languages (id)
            )
        """)
        
        # 16. Quiz Answers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER,
                question_id INTEGER,
                selected_option TEXT,
                is_correct BOOLEAN,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (attempt_id) REFERENCES quiz_attempts (id),
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
        """)
        
        # 17. User Book Progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_book_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                book_id INTEGER,
                current_chapter INTEGER DEFAULT 1,
                current_verse INTEGER DEFAULT 1,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                questions_answered INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (book_id) REFERENCES books (id),
                UNIQUE(user_id, book_id)
            )
        """)
        
        # ==================== INSERT INITIAL DATA ====================
        
        # Insert Languages
        languages = [
            ('en', 'English', 'English', 1),
            ('am', 'Amharic', 'አማርኛ', 1),
            ('or', 'Oromo', 'Afaan Oromoo', 1),
            ('ti', 'Tigrinya', 'ትግርኛ', 1)
        ]
        for code, name, native, active in languages:
            cursor.execute("""
                INSERT OR IGNORE INTO languages (code, name, native_name, is_active)
                VALUES (?, ?, ?, ?)
            """, (code, name, native, active))
        
        # Insert Levels
        levels = [
            (1, 'Easy', 'Basic questions directly from the text', '🌟', '#4CAF50'),
            (2, 'Medium', 'Questions about meaning and context', '⭐', '#FF9800'),
            (3, 'Hard', 'In-depth questions requiring deep understanding', '🏆', '#F44336')
        ]
        for num, name, desc, icon, color in levels:
            cursor.execute("""
                INSERT OR IGNORE INTO levels (level_number, name, description, icon, color)
                VALUES (?, ?, ?, ?, ?)
            """, (num, name, desc, icon, color))
        
        # Insert testaments
        cursor.execute("INSERT OR IGNORE INTO testaments (id, name) VALUES (1, 'Old')")
        cursor.execute("INSERT OR IGNORE INTO testaments (id, name) VALUES (2, 'New')")
        
        conn.commit()

        # Bootstrap admin account from environment if configured
        admin_username = os.environ.get('ADMIN_USERNAME')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        admin_email = os.environ.get('ADMIN_EMAIL')
        if admin_username and admin_password:
            cursor.execute("SELECT id, is_admin FROM users WHERE username = ?", (admin_username,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE users SET is_admin = 1, updated_at = ? WHERE id = ?",
                    (datetime.utcnow(), existing[0])
                )
            else:
                salt = secrets.token_hex(16)
                password_hash = hashlib.sha256(f"{admin_password}{salt}".encode()).hexdigest()
                password_hash = f"{salt}:{password_hash}"
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, created_at, updated_at, is_active, is_admin)
                    VALUES (?, ?, ?, ?, ?, 1, 1)
                """, (
                    admin_username,
                    admin_email,
                    password_hash,
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
            conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        conn.close()
        
        print("✅ Database initialized successfully!")
        print(f"📊 Tables created ({len(tables)} tables):")
        for table in tables:
            print(f"   - {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    init_database()