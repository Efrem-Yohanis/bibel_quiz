# app/routes/user.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import sys
from pathlib import Path
from flasgger import Swagger
from flasgger.utils import swag_from
user_bp = Blueprint('user', __name__)

# Helper function for database connection
def get_db():
    """Get database connection"""
    import sqlite3
    DB_PATH = Path(__file__).parent.parent / 'bible_quiz.db'
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== GET /api/users/profile ====================

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile
    ---
    tags:
      - User Profile
    summary: Get current user profile
    description: Returns the profile information of the authenticated user
    security:
      - BearerAuth: []
    responses:
      200:
        description: Profile retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: john_doe
                email:
                  type: string
                  example: john@example.com
                created_at:
                  type: string
                  format: date-time
                total_quizzes_taken:
                  type: integer
                  example: 5
                total_correct_answers:
                  type: integer
                  example: 42
                total_questions_answered:
                  type: integer
                  example: 50
      401:
        description: Unauthorized - Invalid or missing token
      404:
        description: User not found
      500:
        description: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, created_at, 
                   total_quizzes_taken, total_correct_answers, total_questions_answered
            FROM users WHERE id = ? AND is_active = 1
        """, (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at'],
                'total_quizzes_taken': user['total_quizzes_taken'] or 0,
                'total_correct_answers': user['total_correct_answers'] or 0,
                'total_questions_answered': user['total_questions_answered'] or 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get profile: {str(e)}'
        }), 500


# ==================== GET /api/users/profile/complete ====================

@user_bp.route('/profile/complete', methods=['GET'])
@jwt_required()
def get_complete_profile():
    """Get complete user profile with all history and progress
    ---
    tags:
      - User Profile
    summary: Get complete user profile
    description: Returns complete profile including quiz history, in-progress quizzes, and statistics
    security:
      - BearerAuth: []
    responses:
      200:
        description: Complete profile retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                user:
                  type: object
                statistics:
                  type: object
                quiz_history:
                  type: array
                in_progress_quizzes:
                  type: array
                can_resume:
                  type: boolean
    """
    try:
        user_id = get_jwt_identity()
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user basic info
        cursor.execute("""
            SELECT id, username, email, created_at, last_login,
                   total_quizzes_taken, total_correct_answers, total_questions_answered
            FROM users WHERE id = ? AND is_active = 1
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Calculate accuracy
        accuracy = 0
        if user['total_questions_answered'] > 0:
            accuracy = (user['total_correct_answers'] / user['total_questions_answered']) * 100
        
        # Get quiz history - only select columns that exist
        # First check what columns are available
        cursor.execute("PRAGMA table_info(quiz_attempts)")
        available_columns = [col[1] for col in cursor.fetchall()]
        
        # Build select clause based on available columns
        select_fields = ['id', 'total_questions', 'completed_at']
        if 'book_id' in available_columns:
            select_fields.append('book_id')
        if 'correct_answers' in available_columns:
            select_fields.append('correct_answers')
        if 'score_percentage' in available_columns:
            select_fields.append('score_percentage')
        
        select_clause = ', '.join(select_fields)
        
        cursor.execute(f"""
            SELECT {select_clause}
            FROM quiz_attempts 
            WHERE user_id = ? AND status = 'completed'
            ORDER BY completed_at DESC
            LIMIT 20
        """, (user_id,))
        
        quiz_history = []
        for row in cursor.fetchall():
            history_item = {
                'id': row['id'],
                'total_questions': row['total_questions'],
                'completed_at': row['completed_at']
            }
            if 'book_id' in select_fields and 'book_id' in row.keys():
                history_item['book_id'] = row['book_id']
            if 'correct_answers' in select_fields and 'correct_answers' in row.keys():
                history_item['correct_answers'] = row['correct_answers']
            if 'score_percentage' in select_fields and 'score_percentage' in row.keys():
                history_item['score_percentage'] = row['score_percentage']
            quiz_history.append(history_item)
        
        # Get in-progress quizzes
        select_fields = ['id', 'total_questions', 'started_at']
        if 'book_id' in available_columns:
            select_fields.append('book_id')
        if 'correct_answers' in available_columns:
            select_fields.append('correct_answers')
        if 'answered_questions' in available_columns:
            select_fields.append('answered_questions')
        if 'score_percentage' in available_columns:
            select_fields.append('score_percentage')
        
        select_clause = ', '.join(select_fields)
        
        cursor.execute(f"""
            SELECT {select_clause}
            FROM quiz_attempts 
            WHERE user_id = ? AND status = 'in_progress'
            ORDER BY started_at DESC
        """, (user_id,))
        
        in_progress = []
        for row in cursor.fetchall():
            progress_item = {
                'id': row['id'],
                'total_questions': row['total_questions'],
                'started_at': row['started_at']
            }
            if 'book_id' in select_fields and 'book_id' in row.keys():
                progress_item['book_id'] = row['book_id']
            if 'correct_answers' in select_fields and 'correct_answers' in row.keys():
                progress_item['correct_answers'] = row['correct_answers']
            if 'answered_questions' in select_fields and 'answered_questions' in row.keys():
                progress_item['answered_questions'] = row['answered_questions']
            if 'score_percentage' in select_fields and 'score_percentage' in row.keys():
                progress_item['score_percentage'] = row['score_percentage']
            in_progress.append(progress_item)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'member_since': user['created_at'],
                    'last_login': user['last_login']
                },
                'statistics': {
                    'total_quizzes_taken': user['total_quizzes_taken'] or 0,
                    'total_questions_answered': user['total_questions_answered'] or 0,
                    'total_correct_answers': user['total_correct_answers'] or 0,
                    'accuracy_percentage': round(accuracy, 2)
                },
                'quiz_history': quiz_history,
                'in_progress_quizzes': in_progress,
                'can_resume': len(in_progress) > 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500



# ==================== GET /api/users/profile/summary ====================

@user_bp.route('/profile/summary', methods=['GET'])
@jwt_required()
def get_profile_summary():
    """Get profile summary (lightweight version)
    ---
    tags:
      - User Profile
    summary: Get profile summary
    description: Returns a lightweight version of user profile with essential statistics
    security:
      - BearerAuth: []
    responses:
      200:
        description: Profile summary retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            profile:
              type: object
              properties:
                user:
                  type: object
                statistics:
                  type: object
                can_resume:
                  type: boolean
                recent_activity:
                  type: array
                in_progress_count:
                  type: integer
      401:
        description: Unauthorized
      404:
        description: User not found
    """
    try:
        user_id = get_jwt_identity()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, created_at, last_login,
                   total_quizzes_taken, total_correct_answers, total_questions_answered
            FROM users WHERE id = ? AND is_active = 1
        """, (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        accuracy = 0
        if user['total_questions_answered'] > 0:
            accuracy = (user['total_correct_answers'] / user['total_questions_answered']) * 100
        
        summary = {
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'member_since': user['created_at'],
                'last_login': user['last_login']
            },
            'statistics': {
                'total_quizzes_taken': user['total_quizzes_taken'] or 0,
                'total_questions_answered': user['total_questions_answered'] or 0,
                'total_correct_answers': user['total_correct_answers'] or 0,
                'accuracy_percentage': round(accuracy, 2)
            },
            'can_resume': False,
            'recent_activity': [],
            'in_progress_count': 0
        }
        
        return jsonify({
            'success': True,
            'profile': summary
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get profile summary: {str(e)}'
        }), 500


# ==================== PUT /api/users/profile ====================

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile
    ---
    tags:
      - User Profile
    summary: Update user profile
    description: Update the authenticated user's profile information
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              minLength: 3
              maxLength: 50
              example: new_username
            email:
              type: string
              format: email
              example: newemail@example.com
    responses:
      200:
        description: Profile updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Profile updated successfully
            user:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
                email:
                  type: string
      400:
        description: Update failed - username or email already taken
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if data.get('username'):
            # Check if username exists
            cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", 
                         (data['username'], user_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Username already taken'}), 400
            updates.append("username = ?")
            params.append(data['username'])
        
        if data.get('email'):
            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", 
                         (data['email'], user_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
            updates.append("email = ?")
            params.append(data['email'])
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow())
            params.append(user_id)
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        # Get updated user
        cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }), 500


# ==================== GET /api/users/stats ====================

@user_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get user statistics
    ---
    tags:
      - User Profile
    summary: Get user statistics
    description: Returns detailed statistics about user's quiz performance
    security:
      - BearerAuth: []
    responses:
      200:
        description: Statistics retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            statistics:
              type: object
              properties:
                total_quizzes_taken:
                  type: integer
                total_questions_answered:
                  type: integer
                total_correct_answers:
                  type: integer
                accuracy_percentage:
                  type: number
                member_since:
                  type: string
                last_login:
                  type: string
                recent_attempts:
                  type: array
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT created_at, last_login, total_quizzes_taken, 
                   total_correct_answers, total_questions_answered
            FROM users WHERE id = ?
        """, (user_id,))
        
        user = cursor.fetchone()
        
        # Get recent attempts
        cursor.execute("""
            SELECT completed_at as date, score_percentage as score, total_questions 
            FROM quiz_attempts 
            WHERE user_id = ? AND status = 'completed'
            ORDER BY completed_at DESC 
            LIMIT 10
        """, (user_id,))
        
        attempts = cursor.fetchall()
        conn.close()
        
        accuracy = 0
        if user and user['total_questions_answered'] > 0:
            accuracy = (user['total_correct_answers'] / user['total_questions_answered']) * 100
        
        stats = {
            'total_quizzes_taken': user['total_quizzes_taken'] if user else 0,
            'total_questions_answered': user['total_questions_answered'] if user else 0,
            'total_correct_answers': user['total_correct_answers'] if user else 0,
            'accuracy_percentage': round(accuracy, 2),
            'member_since': user['created_at'] if user else None,
            'last_login': user['last_login'] if user else None,
            'recent_attempts': [
                {
                    'date': attempt['date'],
                    'score': round(attempt['score'], 2) if attempt['score'] else 0,
                    'total_questions': attempt['total_questions']
                }
                for attempt in attempts
            ]
        }
        
        return jsonify({
            'success': True,
            'statistics': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get statistics: {str(e)}'
        }), 500


# ==================== GET /api/users/progress/{book_name} ====================

@user_bp.route('/progress/<book_name>', methods=['GET'])
@jwt_required()
def get_book_progress(book_name):
    """Get user's progress for a specific book
    ---
    tags:
      - User Profile
    summary: Get book progress
    description: Returns the user's reading/progress for a specific book
    security:
      - BearerAuth: []
    parameters:
      - name: book_name
        in: path
        required: true
        type: string
        example: Genesis
        description: Name of the book
    responses:
      200:
        description: Progress retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            book_name:
              type: string
            progress:
              type: object
              properties:
                book_name:
                  type: string
                current_chapter:
                  type: integer
                current_verse:
                  type: integer
                questions_answered:
                  type: integer
                correct_answers:
                  type: integer
                completed:
                  type: boolean
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get book_id from book_name
        cursor.execute("SELECT id FROM books WHERE name = ?", (book_name,))
        book = cursor.fetchone()
        
        if not book:
            conn.close()
            return jsonify({
                'success': True,
                'book_name': book_name,
                'progress': {
                    'book_name': book_name,
                    'current_chapter': 1,
                    'current_verse': 1,
                    'questions_answered': 0,
                    'correct_answers': 0,
                    'completed': False
                }
            }), 200
        
        book_id = book['id']
        
        # Get progress
        cursor.execute("""
            SELECT current_chapter, current_verse, questions_answered, correct_answers, completed
            FROM user_book_progress 
            WHERE user_id = ? AND book_id = ?
        """, (user_id, book_id))
        
        progress = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'book_name': book_name,
            'progress': {
                'book_name': book_name,
                'current_chapter': progress['current_chapter'] if progress else 1,
                'current_verse': progress['current_verse'] if progress else 1,
                'questions_answered': progress['questions_answered'] if progress else 0,
                'correct_answers': progress['correct_answers'] if progress else 0,
                'completed': progress['completed'] if progress else False
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get book progress: {str(e)}'
        }), 500


# ==================== POST /api/users/update-progress ====================

@user_bp.route('/update-progress', methods=['POST'])
@jwt_required()
def update_progress():
    """Update user's progress in a book
    ---
    tags:
      - User Profile
    summary: Update book progress
    description: Update the user's reading/progress for a specific book
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - book_name
          properties:
            book_name:
              type: string
              example: Genesis
              description: Name of the book
            chapter:
              type: integer
              example: 5
              description: Current chapter
            verse:
              type: integer
              example: 10
              description: Current verse
    responses:
      200:
        description: Progress updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Progress updated successfully
      400:
        description: Missing book name
      401:
        description: Unauthorized
      404:
        description: Book not found
      500:
        description: Server error
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('book_name'):
            return jsonify({
                'success': False,
                'message': 'Book name is required'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get book_id
        cursor.execute("SELECT id FROM books WHERE name = ?", (data['book_name'],))
        book = cursor.fetchone()
        
        if not book:
            conn.close()
            return jsonify({'success': False, 'message': f'Book "{data["book_name"]}" not found'}), 404
        
        book_id = book['id']
        chapter = data.get('chapter', 1)
        verse = data.get('verse', 1)
        
        # Insert or update progress
        cursor.execute("""
            INSERT INTO user_book_progress (user_id, book_id, current_chapter, current_verse, last_activity)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, book_id) DO UPDATE SET
                current_chapter = ?,
                current_verse = ?,
                last_activity = ?
        """, (user_id, book_id, chapter, verse, datetime.utcnow(), chapter, verse, datetime.utcnow()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Progress updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update progress: {str(e)}'
        }), 500


# ==================== GET /api/users/quiz-history ====================

@user_bp.route('/quiz-history', methods=['GET'])
@jwt_required()
def get_quiz_history():
    """Get user's quiz history
    ---
    tags:
      - User Profile
    summary: Get quiz history
    description: Returns the user's completed quiz history with scores
    security:
      - BearerAuth: []
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: Maximum number of records to return
    responses:
      200:
        description: Quiz history retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            history:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  book_name:
                    type: string
                  total_questions:
                    type: integer
                  correct_answers:
                    type: integer
                  score_percentage:
                    type: number
                  completed_at:
                    type: string
            total:
              type: integer
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 50, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT qa.id, b.name as book_name, qa.total_questions, 
                   qa.correct_answers, qa.score_percentage, qa.completed_at
            FROM quiz_attempts qa
            JOIN books b ON qa.book_id = b.id
            WHERE qa.user_id = ? AND qa.status = 'completed'
            ORDER BY qa.completed_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'history': history,
            'total': len(history)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get quiz history: {str(e)}'
        }), 500


# ==================== GET /api/users/in-progress-quizzes ====================

@user_bp.route('/in-progress-quizzes', methods=['GET'])
@jwt_required()
def get_in_progress_quizzes():
    """Get all in-progress quizzes for the user
    ---
    tags:
      - User Profile
    summary: Get in-progress quizzes
    description: Returns all quizzes that the user has started but not completed
    security:
      - BearerAuth: []
    responses:
      200:
        description: In-progress quizzes retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            quizzes:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  book_name:
                    type: string
                  total_questions:
                    type: integer
                  answered_questions:
                    type: integer
                  correct_answers:
                    type: integer
                  score_percentage:
                    type: number
                  started_at:
                    type: string
            count:
              type: integer
            can_resume:
              type: boolean
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        user_id = get_jwt_identity()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT qa.id, b.name as book_name, qa.total_questions, 
                   qa.answered_questions, qa.correct_answers, 
                   qa.score_percentage, qa.started_at
            FROM quiz_attempts qa
            JOIN books b ON qa.book_id = b.id
            WHERE qa.user_id = ? AND qa.status = 'in_progress'
            ORDER BY qa.started_at DESC
        """, (user_id,))
        
        quizzes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'quizzes': quizzes,
            'count': len(quizzes),
            'can_resume': len(quizzes) > 0
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get in-progress quizzes: {str(e)}'
        }), 500