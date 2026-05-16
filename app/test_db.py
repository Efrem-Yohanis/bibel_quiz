# test_db.py
import sqlite3

conn = sqlite3.connect('bible_quiz.db')
cursor = conn.cursor()

# Check Bible verses
print("="*60)
print("📖 BIBLE VERSE TEST")
print("="*60)

# Count verses by language
cursor.execute("SELECT language, COUNT(*) FROM verse_texts GROUP BY language")
print("\n📊 Verse counts:")
for lang, count in cursor.fetchall():
    lang_name = {'en': 'English', 'am': 'Amharic', 'or': 'Oromo'}.get(lang, lang)
    print(f"   {lang_name}: {count} verses")

# Get a sample verse
cursor.execute("""
    SELECT b.name, c.chapter_number, v.verse_number, vt.text, vt.language
    FROM verse_texts vt
    JOIN verses v ON vt.verse_id = v.id
    JOIN chapters c ON v.chapter_id = c.id
    JOIN books b ON c.book_id = b.id
    LIMIT 5
""")

print("\n📖 Sample verses:")
for row in cursor.fetchall():
    print(f"   {row[0]} {row[1]}:{row[2]} ({row[4]}) - {row[3][:60]}...")

# Check Genesis 1:1 in all languages
print("\n📖 Genesis 1:1 in all languages:")
for lang in ['en', 'am', 'or']:
    cursor.execute("""
        SELECT vt.text FROM verse_texts vt
        JOIN verses v ON vt.verse_id = v.id
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        WHERE b.name = 'Genesis' AND c.chapter_number = 1 
        AND v.verse_number = 1 AND vt.language = ?
    """, (lang,))
    
    result = cursor.fetchone()
    if result:
        lang_name = {'en': 'English', 'am': 'Amharic', 'or': 'Oromo'}.get(lang, lang)
        print(f"   {lang_name}: {result[0][:80]}...")

conn.close()