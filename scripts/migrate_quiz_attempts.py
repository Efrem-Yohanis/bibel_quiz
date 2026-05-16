# scripts/check_quiz_attempts.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'app' / 'bible_quiz.db'

def check():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("="*60)
    print("📊 QUIZ_ATTEMPTS TABLE CHECK")
    print("="*60)
    
    # Check column info
    cursor.execute("PRAGMA table_info(quiz_attempts)")
    columns = cursor.fetchall()
    print("\nColumns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check data
    cursor.execute("SELECT COUNT(*) FROM quiz_attempts")
    count = cursor.fetchone()[0]
    print(f"\nTotal records: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM quiz_attempts LIMIT 1")
        sample = cursor.fetchone()
        print("\nSample record:")
        for i, col in enumerate(columns):
            print(f"  {col[1]}: {sample[i]}")
    
    conn.close()

if __name__ == "__main__":
    check()