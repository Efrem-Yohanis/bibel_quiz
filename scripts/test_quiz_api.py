# app/test_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bible_quiz.db'

def test_database():
    print("="*60)
    print("📖 DATABASE VERIFICATION")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Check Languages
    print("\n📚 LANGUAGES:")
    cursor.execute("SELECT id, code, name, native_name FROM languages")
    languages = cursor.fetchall()
    for lang in languages:
        print(f"   ID: {lang[0]}, Code: {lang[1]}, Name: {lang[2]}, Native: {lang[3]}")
    
    # 2. Check Levels
    print("\n⭐ LEVELS:")
    cursor.execute("SELECT id, level_number, name, description FROM levels")
    levels = cursor.fetchall()
    for level in levels:
        print(f"   ID: {level[0]}, Level: {level[1]}, Name: {level[2]}, Desc: {level[3][:50]}...")
    
    # 3. Check Testaments
    print("\n📖 TESTAMENTS:")
    cursor.execute("SELECT id, name FROM testaments")
    testaments = cursor.fetchall()
    for t in testaments:
        print(f"   ID: {t[0]}, Name: {t[1]}")
    
    # 4. Check Books (first 10)
    print("\n📚 BOOKS (first 10):")
    cursor.execute("SELECT id, name, testament_id FROM books LIMIT 10")
    books = cursor.fetchall()
    for book in books:
        print(f"   ID: {book[0]}, Name: {book[1]}, Testament ID: {book[2]}")
    
    # 5. Check Questions count
    print("\n❓ QUESTIONS:")
    cursor.execute("SELECT COUNT(*) FROM questions")
    questions_count = cursor.fetchone()[0]
    print(f"   Total questions: {questions_count}")
    
    # 6. Check questions by level
    print("\n📊 QUESTIONS BY LEVEL:")
    cursor.execute("""
        SELECT l.level_number, l.name, COUNT(q.id) as count
        FROM questions q
        JOIN levels l ON q.level_id = l.id
        GROUP BY l.id
        ORDER BY l.level_number
    """)
    level_counts = cursor.fetchall()
    for level_num, level_name, count in level_counts:
        print(f"   Level {level_num} - {level_name}: {count} questions")
    
    # 7. Check question texts by language
    print("\n🌐 QUESTION TEXTS BY LANGUAGE:")
    cursor.execute("""
        SELECT lang.code, lang.name, COUNT(qt.id) as count
        FROM question_texts qt
        JOIN languages lang ON qt.language_id = lang.id
        GROUP BY lang.id
        ORDER BY lang.id
    """)
    lang_counts = cursor.fetchall()
    for code, name, count in lang_counts:
        print(f"   {name} ({code}): {count} texts")
    
    # 8. Check verses count
    print("\n📖 VERSES:")
    cursor.execute("SELECT COUNT(*) FROM verses")
    verses_count = cursor.fetchone()[0]
    print(f"   Total verses: {verses_count}")
    
    # 9. Check verse texts by language
    print("\n🌐 VERSE TEXTS BY LANGUAGE:")
    cursor.execute("""
        SELECT lang.code, lang.name, COUNT(vt.id) as count
        FROM verse_texts vt
        JOIN languages lang ON vt.language_id = lang.id
        GROUP BY lang.id
        ORDER BY lang.id
    """)
    verse_lang_counts = cursor.fetchall()
    for code, name, count in verse_lang_counts:
        print(f"   {name} ({code}): {count} texts")
    
    # 10. Sample verses
    print("\n📖 SAMPLE VERSES (English):")
    cursor.execute("""
        SELECT b.name, c.chapter_number, v.verse_number, vt.text
        FROM verse_texts vt
        JOIN verses v ON vt.verse_id = v.id
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        JOIN languages l ON vt.language_id = l.id
        WHERE l.code = 'en'
        LIMIT 5
    """)
    samples = cursor.fetchall()
    for sample in samples:
        print(f"   {sample[0]} {sample[1]}:{sample[2]} - {sample[3][:60]}...")
    
    # 11. Sample questions
    print("\n❓ SAMPLE QUESTIONS (English):")
    cursor.execute("""
        SELECT b.name, l.level_number, qt.text
        FROM questions q
        JOIN books b ON q.book_id = b.id
        JOIN levels l ON q.level_id = l.id
        JOIN question_texts qt ON qt.question_id = q.id
        JOIN languages lang ON qt.language_id = lang.id
        WHERE lang.code = 'en'
        LIMIT 5
    """)
    q_samples = cursor.fetchall()
    for sample in q_samples:
        print(f"   {sample[0]} (Level {sample[1]}): {sample[2][:60]}...")
    
    # 12. Quiz attempts count
    print("\n📊 QUIZ ATTEMPTS:")
    cursor.execute("SELECT COUNT(*) FROM quiz_attempts")
    attempts_count = cursor.fetchone()[0]
    print(f"   Total attempts: {attempts_count}")
    
    # 13. Users count
    print("\n👤 USERS:")
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]
    print(f"   Total users: {users_count}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ DATABASE VERIFICATION COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    test_database()






    