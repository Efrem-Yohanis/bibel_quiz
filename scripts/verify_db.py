# scripts/verify_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'app' / 'bible_quiz.db'

def verify_database():
    print("="*60)
    print("📊 DATABASE VERIFICATION")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check Books
    cursor.execute("SELECT COUNT(*) FROM books")
    books_count = cursor.fetchone()[0]
    print(f"\n📚 Books: {books_count}")
    if books_count > 0:
        cursor.execute("SELECT id, name FROM books LIMIT 5")
        books = cursor.fetchall()
        for book in books:
            print(f"   - {book[0]}: {book[1]}")
    
    # Check Questions
    cursor.execute("SELECT COUNT(*) FROM questions")
    questions_count = cursor.fetchone()[0]
    print(f"\n❓ Questions: {questions_count}")
    
    if questions_count > 0:
        cursor.execute("""
            SELECT b.name, q.level, COUNT(*) as count 
            FROM questions q
            JOIN books b ON q.book_id = b.id
            GROUP BY b.name, q.level
            LIMIT 10
        """)
        questions = cursor.fetchall()
        for q in questions:
            print(f"   - {q[0]} (Level {q[1]}): {q[2]} questions")
    
    # Check Question Texts
    cursor.execute("SELECT language, COUNT(*) FROM question_texts GROUP BY language")
    question_texts = cursor.fetchall()
    print(f"\n📝 Question Texts by Language:")
    for lang, count in question_texts:
        lang_name = {'en': 'English', 'am': 'Amharic', 'or': 'Oromo'}.get(lang, lang)
        print(f"   - {lang_name}: {count}")
    
    # Check Options
    cursor.execute("SELECT COUNT(*) FROM options")
    options_count = cursor.fetchone()[0]
    print(f"\n🔘 Options: {options_count}")
    
    # Sample question with options
    if questions_count > 0:
        cursor.execute("""
            SELECT q.id, qt.text, o.label, ot.text
            FROM questions q
            JOIN question_texts qt ON qt.question_id = q.id
            JOIN options o ON o.question_id = q.id
            JOIN option_texts ot ON ot.option_id = o.id
            WHERE qt.language = 'en'
            LIMIT 1
        """)
        sample = cursor.fetchone()
        if sample:
            print(f"\n📖 Sample Question:")
            print(f"   ID: {sample[0]}")
            print(f"   Text: {sample[1][:100]}...")
            print(f"   Options: {sample[2]}: {sample[3][:50]}...")
    
    conn.close()
    
    print("\n" + "="*60)
    if books_count > 0 and questions_count > 0:
        print("✅ Database is ready for Quiz API!")
    else:
        print("⚠️ Database needs data. Run import scripts first.")
    print("="*60)

if __name__ == "__main__":
    verify_database()