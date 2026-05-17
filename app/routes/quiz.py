# app/routes/quiz.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys
from pathlib import Path
from flasgger import Swagger
from flasgger.utils import swag_from
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from services.quiz_service import QuizService
    quiz_service = QuizService()
    print("✅ QuizService loaded")
except Exception as e:
    print(f"⚠️ QuizService not available: {e}")
    quiz_service = None

quiz_bp = Blueprint('quiz', __name__)

# Base response helper
def base_response(success=True, data=None, message=None, errors=None):
    return {
        'success': success,
        'message': message,
        'data': data or {},
        'errors': errors
    }


# ==================== 1. GET /api/quiz/languages ====================

@quiz_bp.route('/languages', methods=['GET'])
@jwt_required(optional=True)
def get_languages():
    """Get all available languages
    ---
    tags:
      - Quiz
    summary: Get available languages
    responses:
      200:
        description: List of languages
    """
    try:
        if not quiz_service:
            return jsonify(base_response(False, message='Quiz service not available')), 503
        
        languages = quiz_service.get_languages()
        
        return jsonify(base_response(True, data=languages)), 200
        
    except Exception as e:
        return jsonify(base_response(False, message=str(e))), 500


# ==================== 2. GET /api/quiz/books ====================

@quiz_bp.route('/books', methods=['GET'])
@jwt_required(optional=True)
def get_books():
    """Get all books that have questions with level breakdown
    ---
    tags:
      - Quiz
    summary: Get books with questions
    responses:
      200:
        description: List of books with question counts per level
    """
    try:
        if not quiz_service:
            return jsonify(base_response(False, message='Quiz service not available')), 503
        
        books = quiz_service.get_books()
        
        return jsonify(base_response(True, data=books)), 200
        
    except Exception as e:
        return jsonify(base_response(False, message=str(e))), 500


# ==================== 3. GET /api/quiz/books/{book_id}/levels ====================

@quiz_bp.route('/books/<int:book_id>/levels', methods=['GET'])
@jwt_required(optional=True)
def get_book_levels(book_id):
    """Get available levels for a specific book
    ---
    tags:
      - Quiz
    summary: Get levels for a book
    parameters:
      - name: book_id
        in: path
        required: true
        type: integer
        description: Book ID
    responses:
      200:
        description: Available levels with details
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                book_id:
                  type: integer
                book_name:
                  type: string
                levels:
                  type: array
                  items:
                    type: object
                    properties:
                      level_id:
                        type: integer
                      level_number:
                        type: integer
                      name:
                        type: string
                      description:
                        type: string
                      icon:
                        type: string
                      color:
                        type: string
    """
    try:
        if not quiz_service:
            return jsonify(base_response(False, message='Quiz service not available')), 503
        
        # Get unique levels for this book
        conn = quiz_service.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT l.id as level_id, l.level_number, l.name, 
                            l.description, l.icon, l.color
            FROM questions q
            JOIN levels l ON q.level_id = l.id
            WHERE q.book_id = ?
            ORDER BY l.level_number
        """, (book_id,))
        
        levels = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Get book name
        book_name = quiz_service.get_book_name(book_id)
        
        return jsonify(base_response(True, data={
            'book_id': book_id,
            'book_name': book_name,
            'levels': levels
        })), 200
        
    except Exception as e:
        return jsonify(base_response(False, message=str(e))), 500


# ==================== 4. GET /api/quiz/quizzes ====================

@quiz_bp.route('/quizzes', methods=['GET'])
@jwt_required(optional=True)
def get_quizzes():
    """Get quizzes by book and level
    ---
    tags:
      - Quiz
    summary: Get quizzes list
    parameters:
      - name: book_id
        in: query
        required: true
        type: integer
      - name: level_id
        in: query
        required: true
        type: integer
    responses:
      200:
        description: List of quizzes (by chapter)
    """
    try:
        if not quiz_service:
            return jsonify(base_response(False, message='Quiz service not available')), 503
        
        book_id = request.args.get('book_id', type=int)
        level_id = request.args.get('level_id', type=int)
        
        if not book_id or not level_id:
            return jsonify(base_response(False, message='book_id and level_id are required')), 400
        
        # Get quizzes (chapters) for this book and level
        conn = quiz_service.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT 
                c.chapter_number as quiz_id,
                COUNT(q.id) as total_questions
            FROM questions q
            JOIN chapters c ON q.chapter_id = c.id
            WHERE q.book_id = ? AND q.level_id = ?
            GROUP BY c.chapter_number
            ORDER BY c.chapter_number
        """, (book_id, level_id))
        
        chapters = cursor.fetchall()
        conn.close()
        
        book_name = quiz_service.get_book_name(book_id)
        
        quizzes = []
        for chapter in chapters:
            quizzes.append({
                'quiz_id': chapter['quiz_id'],
                'title': f"{book_name} Chapter {chapter['quiz_id']} Quiz",
                'total_questions': chapter['total_questions'],
                'chapter': chapter['quiz_id']
            })
        
        return jsonify(base_response(True, data={
            'book_id': book_id,
            'book_name': book_name,
            'level_id': level_id,
            'quizzes': quizzes
        })), 200
        
    except Exception as e:
        return jsonify(base_response(False, message=str(e))), 500


# ==================== 5. POST /api/quiz/quiz/start ====================

@quiz_bp.route('/quiz/start', methods=['POST'])
@jwt_required()
def start_quiz():
    """Start a new quiz
    ---
    tags:
      - Quiz
    summary: Start a new quiz session
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - book_id
            - level_id
            - language_id
          properties:
            book_id:
              type: integer
            level_id:
              type: integer
            language_id:
              type: integer
    responses:
      201:
        description: Quiz started
    """
    try:
        if not quiz_service:
            return jsonify(base_response(False, message='Quiz service not available')), 503
        
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('book_id') or not data.get('level_id') or not data.get('language_id'):
            return jsonify(base_response(False, message='book_id, level_id, and language_id are required')), 400
        
        result = quiz_service.start_quiz(
            user_id=user_id,
            book_id=data['book_id'],
            level_id=data['level_id'],
            language_id=data['language_id']
        )
        
        if 'error' in result:
            return jsonify(base_response(False, message=result['error'])), 400
        
        return jsonify(base_response(True, data=result)), 201
        
    except Exception as e:
        return jsonify(base_response(False, message=str(e))), 500


# ==================== 6. GET /api/quiz/quiz/{attempt_id}/next ====================

@quiz_bp.route('/quiz/<int:attempt_id>/next', methods=['GET'])
@jwt_required()
def get_next_question(attempt_id):
    """Get next question (ONE at a time)
    ---
    tags:
      - Quiz
    summary: Get next quiz question
    security:
      - BearerAuth: []
    parameters:
      - name: attempt_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Next question
    """
    try:
        if not quiz_service:
            return jsonify(base_response(False, message='Quiz service not available')), 503
        
        user_id = get_jwt_identity()
        
        result = quiz_service.get_next_question(attempt_id, user_id)
        
        if 'error' in result:
            return jsonify(base_response(False, message=result['error'])), 400
        
        if result.get('completed'):
            return jsonify(base_response(True, data={'completed': True, 'message': 'Quiz completed'})), 200
        
        return jsonify(base_response(True, data=result)), 200
        
    except Exception as e:
        return jsonify(base_response(False, message=str(e))), 500


# ==================== 7. POST /api/quiz/quiz/answer ====================

@quiz_bp.route('/quiz/answer', methods=['POST'])
@jwt_required()
def submit_answer():
    """Submit answer (core logic)
    ---
    tags:
      - Quiz
    summary: Submit answer for current question
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - attempt_id
            - question_id
            - selected_option
          properties:
            attempt_id:
              type: integer
            question_id:
              type: integer
            selected_option:
              type: string
    responses:
      200:
        description: Answer processed
    """
    try:
        if not quiz_service:
            return jsonify(base_response(False, message='Quiz service not available')), 503
        
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('attempt_id') or not data.get('question_id') or not data.get('selected_option'):
            return jsonify(base_response(False, message='attempt_id, question_id, and selected_option are required')), 400
        
        result = quiz_service.submit_answer(
            attempt_id=data['attempt_id'],
            user_id=user_id,
            question_id=data['question_id'],
            selected_option=data['selected_option']
        )
        
        if 'error' in result:
            return jsonify(base_response(False, message=result['error'])), 400
        
        return jsonify(base_response(True, data=result)), 200
        
    except Exception as e:
        return jsonify(base_response(False, message=str(e))), 500


# ==================== 8. POST /api/quiz/quiz/{attempt_id}/finish ====================

@quiz_bp.route('/quiz/<int:attempt_id>/finish', methods=['POST'])
@jwt_required()
def finish_quiz(attempt_id):
    """Finish quiz and get final score
    ---
    tags:
      - Quiz
    summary: Complete quiz
    security:
      - BearerAuth: []
    parameters:
      - name: attempt_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Quiz results
    """
    try:
        if not quiz_service:
            return jsonify(base_response(False, message='Quiz service not available')), 503
        
        user_id = get_jwt_identity()
        
        result = quiz_service.finish_quiz(attempt_id, user_id)
        
        if 'error' in result:
            return jsonify(base_response(False, message=result['error'])), 400
        
        return jsonify(base_response(True, data=result)), 200
        
    except Exception as e:
        return jsonify(base_response(False, message=str(e))), 500


# ==================== 9. GET /api/quiz/quiz/{attempt_id}/review ====================

@quiz_bp.route('/quiz/<int:attempt_id>/review', methods=['GET'])
@jwt_required()
def get_quiz_review(attempt_id):
    """Get full quiz review
    ---
    tags:
      - Quiz
    summary: Get quiz review with all answers
    security:
      - BearerAuth: []
    parameters:
      - name: attempt_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Quiz review with answers and explanations
    """
    try:
        if not quiz_service:
            return jsonify(base_response(False, message='Quiz service not available')), 503
        
        user_id = get_jwt_identity()
        
        result = quiz_service.get_quiz_review(attempt_id, user_id)
        
        if 'error' in result:
            return jsonify(base_response(False, message=result['error'])), 400
        
        return jsonify(base_response(True, data=result)), 200
        
    except Exception as e:
        return jsonify(base_response(False, message=str(e))), 500