# scripts/check_db_tables.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'app' / 'bible_quiz.db'

def check_tables():
    print("="*60)
    print("📊 CHECKING DATABASE TABLES")
    print("="*60)
    print(f"Database path: {DB_PATH}")
    print(f"Database exists: {DB_PATH.exists()}")
    
    if not DB_PATH.exists():
        print("❌ Database file not found!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\n📋 Tables in database ({len(tables)}):")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Check specific required tables
    required_tables = ['languages', 'levels', 'testaments', 'books', 'chapters', 'questions']
    print("\n✅ Required tables check:")
    for table in required_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        exists = cursor.fetchone()
        status = "✅" if exists else "❌"
        print(f"   {status} {table}")
    
    conn.close()

if __name__ == "__main__":
    check_tables()