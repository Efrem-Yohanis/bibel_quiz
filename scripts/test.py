# scripts/migrate_sqlite_to_postgres_fast.py
"""
High-speed migration from SQLite to PostgreSQL with batch processing
Optimized for 500k+ rows - No special permissions required
Run: python scripts/migrate_sqlite_to_postgres_fast.py
"""

import sqlite3
import psycopg2
import psycopg2.extras
from pathlib import Path
import os
import sys
import time
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============ CONFIGURATION ============
SQLITE_PATH = Path(__file__).parent.parent / 'app' / 'bible_quiz.db'
POSTGRES_URL = "postgresql://bibel_quiz_user:IBQceDb477BJ0i7DWL4MSIOy6hnkATEO@dpg-d84b0f58nd3s73ctqle0-a.oregon-postgres.render.com/bibel_quiz?sslmode=require"

# Performance settings (adjusted for Render PostgreSQL)
BATCH_SIZE = 5000  # Rows per batch (reduced for stability)
PARALLEL_WORKERS = 2  # Reduced for Render's free tier
COMMIT_INTERVAL = 25000  # Commit after every 25k rows

class FastDataMigrator:
    def __init__(self):
        self.sqlite_conn = None
        self.pg_conn = None
        self.pg_cursor = None
        self.stats = {}
        
    def connect(self):
        """Connect to both databases with optimized settings"""
        if not SQLITE_PATH.exists():
            print(f"❌ SQLite database not found at {SQLITE_PATH}")
            return False
            
        # SQLite: Read-only mode for better performance
        self.sqlite_conn = sqlite3.connect(f'file:{SQLITE_PATH}?mode=ro', uri=True)
        self.sqlite_conn.row_factory = sqlite3.Row
        print("✅ Connected to SQLite database (read-only mode)")
        
        try:
            # PostgreSQL: Standard connection without special permissions
            self.pg_conn = psycopg2.connect(
                POSTGRES_URL,
                connect_timeout=30,
                keepalives=1,
                keepalives_idle=5,
                keepalives_interval=2,
                keepalives_count=3
            )
            self.pg_cursor = self.pg_conn.cursor()
            
            # Only use allowed settings
            self.pg_cursor.execute("SET statement_timeout = 0")
            self.pg_cursor.execute("SET lock_timeout = 0")
            
            print("✅ Connected to PostgreSQL database")
            
            # Test connection
            self.pg_cursor.execute("SELECT version()")
            version = self.pg_cursor.fetchone()[0]
            print(f"   PostgreSQL version: {version[:50]}...")
            
            return True
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    def close(self):
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_cursor:
            self.pg_cursor.close()
        if self.pg_conn:
            self.pg_conn.close()
        print("\n✅ Connections closed")
    
    def get_tables(self):
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    
    def get_table_row_count(self, table_name):
        """Get row count for a table"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    
    def preview_all_counts(self):
        """Show row counts for all tables before migration"""
        print("\n" + "="*60)
        print("📊 PRE-MIGRATION ROW COUNTS")
        print("="*60)
        
        tables = self.get_tables()
        total_rows = 0
        table_counts = {}
        
        for table in tables:
            count = self.get_table_row_count(table)
            table_counts[table] = count
            total_rows += count
            
            # Format with commas
            count_str = f"{count:,}"
            print(f"  {table:25} : {count_str:>12}")
        
        print("-"*60)
        print(f"  {'TOTAL':25} : {total_rows:>12,}")
        print("="*60)
        
        return table_counts, total_rows
    
    def create_tables_if_not_exist(self):
        """Create tables only if they don't exist"""
        print("\n📦 Creating tables if not exist...")
        
        # First, get existing tables from PostgreSQL
        self.pg_cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in self.pg_cursor.fetchall()]
        
        # Table definitions (simplified for speed)
        table_definitions = {
            'languages': """
                CREATE TABLE IF NOT EXISTS languages (
                    id INTEGER PRIMARY KEY,
                    code VARCHAR(10),
                    name VARCHAR(50),
                    native_name VARCHAR(100),
                    is_active BOOLEAN,
                    created_at TIMESTAMP
                )
            """,
            'levels': """
                CREATE TABLE IF NOT EXISTS levels (
                    id INTEGER PRIMARY KEY,
                    level_number INTEGER,
                    name VARCHAR(50),
                    description TEXT,
                    icon VARCHAR(50),
                    color VARCHAR(20),
                    created_at TIMESTAMP
                )
            """,
            'testaments': """
                CREATE TABLE IF NOT EXISTS testaments (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(50)
                )
            """,
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username VARCHAR(50),
                    email VARCHAR(100),
                    password_hash VARCHAR(255),
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN,
                    total_quizzes_taken INTEGER,
                    total_correct_answers INTEGER,
                    total_questions_answered INTEGER,
                    reset_token VARCHAR(255),
                    reset_token_expires TIMESTAMP,
                    preferred_language_id INTEGER,
                    is_admin BOOLEAN,
                    google_id VARCHAR(255),
                    auth_provider VARCHAR(50)
                )
            """,
            'books': """
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    testament_id INTEGER
                )
            """,
            'chapters': """
                CREATE TABLE IF NOT EXISTS chapters (
                    id INTEGER PRIMARY KEY,
                    book_id INTEGER,
                    chapter_number INTEGER
                )
            """,
            'verses': """
                CREATE TABLE IF NOT EXISTS verses (
                    id INTEGER PRIMARY KEY,
                    chapter_id INTEGER,
                    verse_number INTEGER
                )
            """,
            'verse_texts': """
                CREATE TABLE IF NOT EXISTS verse_texts (
                    id INTEGER PRIMARY KEY,
                    verse_id INTEGER,
                    language_id INTEGER,
                    text TEXT
                )
            """,
            'questions': """
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY,
                    book_id INTEGER,
                    chapter_id INTEGER,
                    level_id INTEGER,
                    correct_option VARCHAR(1),
                    verse_reference VARCHAR(100),
                    created_at TIMESTAMP
                )
            """,
            'question_texts': """
                CREATE TABLE IF NOT EXISTS question_texts (
                    id INTEGER PRIMARY KEY,
                    question_id INTEGER,
                    language_id INTEGER,
                    text TEXT
                )
            """,
            'options': """
                CREATE TABLE IF NOT EXISTS options (
                    id INTEGER PRIMARY KEY,
                    question_id INTEGER,
                    label VARCHAR(1)
                )
            """,
            'option_texts': """
                CREATE TABLE IF NOT EXISTS option_texts (
                    id INTEGER PRIMARY KEY,
                    option_id INTEGER,
                    language_id INTEGER,
                    text TEXT
                )
            """,
            'explanations': """
                CREATE TABLE IF NOT EXISTS explanations (
                    id INTEGER PRIMARY KEY,
                    question_id INTEGER,
                    language_id INTEGER,
                    text TEXT
                )
            """,
            'user_sessions': """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    token VARCHAR(255),
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    updated_at TIMESTAMP
                )
            """,
            'quiz_attempts': """
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    book_id INTEGER,
                    level_id INTEGER,
                    language_id INTEGER,
                    total_questions INTEGER,
                    answered_questions INTEGER,
                    correct_answers INTEGER,
                    score_percentage REAL,
                    status VARCHAR(20),
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    resume_data TEXT
                )
            """,
            'quiz_answers': """
                CREATE TABLE IF NOT EXISTS quiz_answers (
                    id INTEGER PRIMARY KEY,
                    attempt_id INTEGER,
                    question_id INTEGER,
                    selected_option VARCHAR(1),
                    is_correct BOOLEAN,
                    answered_at TIMESTAMP,
                    user_info TEXT
                )
            """,
            'user_book_progress': """
                CREATE TABLE IF NOT EXISTS user_book_progress (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    book_id INTEGER,
                    current_chapter INTEGER,
                    current_verse INTEGER,
                    last_activity TIMESTAMP,
                    questions_answered INTEGER,
                    correct_answers INTEGER,
                    completed BOOLEAN
                )
            """
        }
        
        for table_name, create_sql in table_definitions.items():
            try:
                self.pg_cursor.execute(create_sql)
                if table_name not in existing_tables:
                    print(f"  ✅ Created table: {table_name}")
                else:
                    print(f"  📋 Table already exists: {table_name}")
            except Exception as e:
                print(f"  ⚠️ Error creating {table_name}: {e}")
        
        self.pg_conn.commit()
    
    def migrate_table_batch(self, table_name, batch_size=BATCH_SIZE):
        """Migrate a single table using batch inserts"""
        start_time = time.time()
        
        # Get total row count
        total_rows = self.get_table_row_count(table_name)
        
        if total_rows == 0:
            print(f"  ⚠️ {table_name}: 0 rows (skipped)")
            return {'table': table_name, 'rows': 0, 'time': 0, 'speed': 0}
        
        # Get column names from SQLite
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Check how many rows already exist in PostgreSQL
        self.pg_cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        existing_rows = self.pg_cursor.fetchone()[0]
        
        if existing_rows >= total_rows:
            print(f"  ✅ {table_name}: Already complete ({existing_rows:,}/{total_rows:,} rows)")
            cursor.close()
            return {'table': table_name, 'rows': existing_rows, 'time': 0, 'speed': 0}
        
        print(f"\n  📊 {table_name}: {total_rows:,} total rows (already have {existing_rows:,})")
        
        # Fetch data in batches from SQLite
        offset = existing_rows
        rows_migrated = existing_rows
        
        while offset < total_rows:
            # Get batch from SQLite
            cursor.execute(f"""
                SELECT * FROM {table_name} 
                ORDER BY id 
                LIMIT {batch_size} 
                OFFSET {offset}
            """)
            
            batch = []
            for row in cursor:
                values = []
                for i, col in enumerate(columns):
                    val = row[i]
                    # Convert boolean for PostgreSQL
                    if col in ['is_active', 'is_admin', 'is_correct', 'completed'] and val is not None:
                        val = bool(val)
                    values.append(val)
                batch.append(tuple(values))
            
            if batch:
                self._insert_batch(table_name, columns, batch)
                rows_migrated += len(batch)
                offset += len(batch)
                
                # Show progress
                percentage = (rows_migrated / total_rows) * 100
                elapsed = time.time() - start_time
                speed = (rows_migrated - existing_rows) / elapsed if elapsed > 0 else 0
                
                print(f"\r    Progress: {percentage:.1f}% ({rows_migrated:,}/{total_rows:,}) | Speed: {speed:.0f} rows/sec", end='')
                
                # Commit periodically
                if rows_migrated % COMMIT_INTERVAL == 0:
                    self.pg_conn.commit()
                    print(f"\n    💾 Committed at {rows_migrated:,} rows")
        
        self.pg_conn.commit()
        
        elapsed = time.time() - start_time
        speed = (rows_migrated - existing_rows) / elapsed if elapsed > 0 else 0
        
        print(f"\n    ✅ Completed: {rows_migrated:,} rows in {elapsed:.1f}s ({speed:.0f} rows/sec)")
        
        cursor.close()
        
        return {
            'table': table_name,
            'rows': rows_migrated,
            'time': elapsed,
            'speed': speed
        }
    
    def _insert_batch(self, table_name, columns, batch):
        """Insert a batch of rows using execute_values for maximum speed"""
        if not batch:
            return
        
        # Use psycopg2.extras.execute_values for fast bulk insert
        columns_str = ','.join(f'"{col}"' for col in columns)
        
        try:
            psycopg2.extras.execute_values(
                self.pg_cursor, 
                f'INSERT INTO "{table_name}" ({columns_str}) VALUES %s ON CONFLICT (id) DO NOTHING', 
                batch, 
                page_size=1000
            )
        except Exception as e:
            print(f"\n    ⚠️ Batch insert failed: {e}")
            # Fallback to individual inserts
            for row in batch:
                try:
                    placeholders = ','.join(['%s'] * len(columns))
                    self.pg_cursor.execute(
                        f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING',
                        row
                    )
                except Exception as insert_error:
                    print(f"\n    ⚠️ Failed to insert row: {insert_error}")
    
    def run(self):
        print("="*60)
        print("🚀 FAST MIGRATION - OPTIMIZED FOR 500K+ ROWS")
        print("="*60)
        
        if not self.connect():
            return
        
        overall_start = time.time()
        
        try:
            # First, show preview of all row counts
            table_counts, total_rows = self.preview_all_counts()
            
            if total_rows == 0:
                print("❌ No data to migrate")
                return
            
            # Ask for confirmation
            print(f"\n⚠️  This will migrate {total_rows:,} total rows to PostgreSQL")
            confirm = input("\nContinue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return
            
            # Create tables if they don't exist
            self.create_tables_if_not_exist()
            
            # Get list of tables to migrate (ordered by dependencies)
            migration_order = ['languages', 'levels', 'testaments', 'users', 'books', 
                              'chapters', 'verses', 'verse_texts', 'questions', 
                              'question_texts', 'options', 'option_texts', 'explanations', 
                              'user_sessions', 'quiz_attempts', 'quiz_answers', 
                              'user_book_progress']
            
            # Filter to only tables that exist in SQLite
            tables_to_migrate = [t for t in migration_order if t in table_counts]
            
            # Migrate sequentially (more stable for Render)
            print("\n💾 Starting migration...")
            results = []
            
            for table in tables_to_migrate:
                print(f"\n  📁 {'='*50}")
                result = self.migrate_table_batch(table)
                results.append(result)
            
            # Summary
            overall_time = time.time() - overall_start
            total_migrated = sum(r['rows'] for r in results)
            total_time_taken = sum(r['time'] for r in results if r['time'] > 0)
            
            print("\n" + "="*60)
            print("📊 MIGRATION SUMMARY")
            print("="*60)
            print(f"✅ Total tables: {len(results)}")
            print(f"✅ Total rows in PostgreSQL: {total_migrated:,}")
            print(f"✅ Total time: {timedelta(seconds=int(overall_time))}")
            
            if total_time_taken > 0:
                avg_speed = total_migrated / total_time_taken
                print(f"✅ Average speed: {avg_speed:.0f} rows/sec")
            
            print("="*60)
            
            # Verify
            self.verify_migration()
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Migration interrupted by user")
            print("✅ Data already migrated is saved in PostgreSQL")
            print("💡 Run the script again to continue where it stopped")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()
    
    def verify_migration(self):
        """Verify that all data was migrated correctly"""
        print("\n" + "="*60)
        print("🔍 VERIFYING MIGRATION")
        print("="*60)
        
        tables = self.get_tables()
        all_match = True
        
        for table in tables:
            sqlite_count = self.get_table_row_count(table)
            
            try:
                self.pg_cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                pg_count = self.pg_cursor.fetchone()[0]
                
                if sqlite_count == pg_count:
                    print(f"  ✅ {table}: {pg_count:,} rows")
                else:
                    print(f"  ⚠️ {table}: SQLite={sqlite_count:,}, PostgreSQL={pg_count:,}")
                    all_match = False
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")
                all_match = False
        
        if all_match:
            print("\n✅ ALL TABLES VERIFIED SUCCESSFULLY!")
        else:
            print("\n⚠️ Some tables have mismatched row counts")
        
        print("="*60)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("⚠️  WARNING: This will migrate ALL data to PostgreSQL")
    print("="*60)
    
    migrator = FastDataMigrator()
    migrator.run()