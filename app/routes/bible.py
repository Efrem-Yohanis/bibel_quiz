# app/routes/bible.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import sys
from pathlib import Path
from flasgger import Swagger
from flasgger.utils import swag_from
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from services.bible_service import BibleService
    bible_service = BibleService()
    print("✅ BibleService loaded")
except Exception as e:
    print(f"⚠️ BibleService not available: {e}")
    bible_service = None

bible_bp = Blueprint('bible', __name__)


@bible_bp.route('/testaments/<testament_name>/books', methods=['GET'])
@jwt_required(optional=True)
def get_books_by_testament(testament_name):
    """Get books by testament with chapter counts
    ---
    tags:
      - Bible
    summary: Get books by testament
    parameters:
      - name: testament_name
        in: path
        type: string
        required: true
        enum: ['Old', 'New']
      - name: language
        in: query
        type: string
        required: false
        default: 'en'
    responses:
      200:
        description: List of books
    """
    try:
        if testament_name not in ['Old', 'New']:
            return jsonify({
                'status': 'error',
                'message': 'Testament must be "Old" or "New"'
            }), 400
        
        if not bible_service:
            return jsonify({'status': 'error', 'message': 'Bible service not available'}), 503
        
        language = request.args.get('language', 'en')
        
        # Get language ID
        conn = bible_service.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM languages WHERE code = ?", (language,))
        lang_row = cursor.fetchone()
        language_id = lang_row['id'] if lang_row else 1
        conn.close()
        
        # Get books by testament
        conn = bible_service.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.id, b.name, COUNT(DISTINCT c.id) as chapters
            FROM books b
            JOIN testaments t ON b.testament_id = t.id
            LEFT JOIN chapters c ON c.book_id = b.id
            WHERE t.name = ?
            GROUP BY b.id
            ORDER BY b.id
        """, (testament_name,))
        
        books = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'testament': testament_name,
            'language': language,
            'books': [dict(row) for row in books]
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bible_bp.route('/books/<book_name>', methods=['GET'])
@jwt_required(optional=True)
def get_book_full_content(book_name):
    """Get full book content with all chapters and verses
    ---
    tags:
      - Bible
    summary: Get full book content
    parameters:
      - name: book_name
        in: path
        type: string
        required: true
      - name: language
        in: query
        type: string
        required: false
        default: 'en'
    responses:
      200:
        description: Complete book with all verses
    """
    try:
        if not bible_service:
            return jsonify({'status': 'error', 'message': 'Bible service not available'}), 503
        
        language = request.args.get('language', 'en')
        
        # Get language ID
        conn = bible_service.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM languages WHERE code = ?", (language,))
        lang_row = cursor.fetchone()
        language_id = lang_row['id'] if lang_row else 1
        conn.close()
        
        # Get book ID
        conn = bible_service.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM books WHERE name LIKE ?", (f'%{book_name}%',))
        book = cursor.fetchone()
        conn.close()
        
        if not book:
            return jsonify({
                'status': 'error',
                'message': f'Book "{book_name}" not found'
            }), 404
        
        book_id = book['id']
        
        # Get all chapters and verses
        conn = bible_service.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.chapter_number, v.verse_number, vt.text
            FROM chapters c
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE c.book_id = ? AND vt.language_id = ?
            ORDER BY c.chapter_number, v.verse_number
        """, (book_id, language_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Organize by chapter
        chapters = {}
        for row in rows:
            chapter = row['chapter_number']
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append({
                'verse': row['verse_number'],
                'text': row['text']
            })
        
        # Convert to list
        chapters_list = [
            {'chapter': ch, 'verses': verses}
            for ch, verses in sorted(chapters.items())
        ]
        
        return jsonify({
            'status': 'success',
            'book': book_name,
            'language': language,
            'chapters': chapters_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bible_bp.route('/books/<book_name>/chapters', methods=['GET'])
@jwt_required(optional=True)
def get_book_chapters(book_name):
    """Get list of chapters (no content, just chapter numbers)
    ---
    tags:
      - Bible
    summary: Get chapters list
    parameters:
      - name: book_name
        in: path
        type: string
        required: true
      - name: language
        in: query
        type: string
        required: false
        default: 'en'
    responses:
      200:
        description: List of chapter numbers
    """
    try:
        if not bible_service:
            return jsonify({'status': 'error', 'message': 'Bible service not available'}), 503
        
        language = request.args.get('language', 'en')
        
        # Get language ID
        conn = bible_service.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM languages WHERE code = ?", (language,))
        lang_row = cursor.fetchone()
        language_id = lang_row['id'] if lang_row else 1
        conn.close()
        
        # Get book ID
        conn = bible_service.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM books WHERE name LIKE ?", (f'%{book_name}%',))
        book = cursor.fetchone()
        conn.close()
        
        if not book:
            return jsonify({
                'status': 'error',
                'message': f'Book "{book_name}" not found'
            }), 404
        
        book_id = book['id']
        
        # Get chapters
        conn = bible_service.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT c.chapter_number
            FROM chapters c
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE c.book_id = ? AND vt.language_id = ?
            ORDER BY c.chapter_number
        """, (book_id, language_id))
        
        chapters = cursor.fetchall()
        conn.close()
        
        chapter_numbers = [row['chapter_number'] for row in chapters]
        
        return jsonify({
            'status': 'success',
            'book': book_name,
            'total_chapters': len(chapter_numbers),
            'chapters': chapter_numbers
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bible_bp.route('/books/<book_name>/chapters/<int:chapter_number>', methods=['GET'])
@jwt_required(optional=True)
def get_chapter_content(book_name, chapter_number):
    """Get specific chapter content
    ---
    tags:
      - Bible
    summary: Get chapter content
    parameters:
      - name: book_name
        in: path
        type: string
        required: true
      - name: chapter_number
        in: path
        type: integer
        required: true
      - name: language
        in: query
        type: string
        required: false
        default: 'en'
    responses:
      200:
        description: Chapter with all verses
    """
    try:
        if not bible_service:
            return jsonify({'status': 'error', 'message': 'Bible service not available'}), 503
        
        language = request.args.get('language', 'en')
        
        # Get language ID
        conn = bible_service.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM languages WHERE code = ?", (language,))
        lang_row = cursor.fetchone()
        language_id = lang_row['id'] if lang_row else 1
        conn.close()
        
        # Get book ID
        conn = bible_service.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM books WHERE name LIKE ?", (f'%{book_name}%',))
        book = cursor.fetchone()
        conn.close()
        
        if not book:
            return jsonify({
                'status': 'error',
                'message': f'Book "{book_name}" not found'
            }), 404
        
        book_id = book['id']
        
        # Get chapter verses
        conn = bible_service.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT v.verse_number, vt.text
            FROM chapters c
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE c.book_id = ? AND c.chapter_number = ? AND vt.language_id = ?
            ORDER BY v.verse_number
        """, (book_id, chapter_number, language_id))
        
        verses = cursor.fetchall()
        conn.close()
        
        if not verses:
            return jsonify({
                'status': 'error',
                'message': f'Chapter {chapter_number} not found in {book_name}'
            }), 404
        
        return jsonify({
            'status': 'success',
            'book': book_name,
            'chapter': chapter_number,
            'language': language,
            'verses': [
                {'verse': row['verse_number'], 'text': row['text']}
                for row in verses
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bible_bp.route('/books/<book_name>/chapters/<int:chapter_number>/verses/<int:verse_number>', methods=['GET'])
@jwt_required(optional=True)
def get_specific_verse(book_name, chapter_number, verse_number):
    """Get specific verse
    ---
    tags:
      - Bible
    summary: Get specific verse
    parameters:
      - name: book_name
        in: path
        type: string
        required: true
      - name: chapter_number
        in: path
        type: integer
        required: true
      - name: verse_number
        in: path
        type: integer
        required: true
      - name: language
        in: query
        type: string
        required: false
        default: 'en'
    responses:
      200:
        description: Specific verse text
    """
    try:
        if not bible_service:
            return jsonify({'status': 'error', 'message': 'Bible service not available'}), 503
        
        language = request.args.get('language', 'en')
        
        # Get language ID
        conn = bible_service.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM languages WHERE code = ?", (language,))
        lang_row = cursor.fetchone()
        language_id = lang_row['id'] if lang_row else 1
        conn.close()
        
        # Get book ID
        conn = bible_service.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM books WHERE name LIKE ?", (f'%{book_name}%',))
        book = cursor.fetchone()
        conn.close()
        
        if not book:
            return jsonify({
                'status': 'error',
                'message': f'Book "{book_name}" not found'
            }), 404
        
        book_id = book['id']
        
        # Get verse
        conn = bible_service.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT vt.text
            FROM chapters c
            JOIN verses v ON v.chapter_id = c.id
            JOIN verse_texts vt ON vt.verse_id = v.id
            WHERE c.book_id = ? AND c.chapter_number = ? 
              AND v.verse_number = ? AND vt.language_id = ?
        """, (book_id, chapter_number, verse_number, language_id))
        
        verse = cursor.fetchone()
        conn.close()
        
        if not verse:
            return jsonify({
                'status': 'error',
                'message': f'Verse {book_name} {chapter_number}:{verse_number} not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'book': book_name,
            'chapter': chapter_number,
            'verse': verse_number,
            'language': language,
            'text': verse['text']
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500