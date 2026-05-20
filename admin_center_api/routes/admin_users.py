# admin_center_api/routes/admin_users.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from admin_center_api.services.user_management_service import UserManagementService

admin_users_bp = Blueprint('admin_users', __name__)
user_service = UserManagementService()


@admin_users_bp.route('/users', methods=['GET'])
def get_all_users():
    """Get all registered users
    ---
    tags:
      - Admin
    summary: Get all registered users
    description: Returns a paginated list of all users with their details
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        default: 100
        description: Number of users to return
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
        description: Number of users to skip
    responses:
      200:
        description: List of users retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                users:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      username:
                        type: string
                      email:
                        type: string
                      created_at:
                        type: string
                      last_login:
                        type: string
                      is_active:
                        type: boolean
                      total_quizzes_taken:
                        type: integer
                      total_correct_answers:
                        type: integer
                      total_questions_answered:
                        type: integer
                total:
                  type: integer
                limit:
                  type: integer
                offset:
                  type: integer
      500:
        description: Server error
    """
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    users = user_service.get_all_users(limit, offset)
    total = user_service.get_user_count()
    
    return jsonify({
        'status': 'success',
        'data': {
            'users': users,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    }), 200


@admin_users_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID
    ---
    tags:
      - Admin
    summary: Get user details
    description: Returns detailed information about a specific user
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
        description: User ID
    responses:
      200:
        description: User details retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
                email:
                  type: string
                created_at:
                  type: string
                last_login:
                  type: string
                is_active:
                  type: boolean
                total_quizzes_taken:
                  type: integer
                total_correct_answers:
                  type: integer
                total_questions_answered:
                  type: integer
      404:
        description: User not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: User not found
    """
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    return jsonify({'status': 'success', 'data': user}), 200


@admin_users_bp.route('/users/<int:user_id>/progress', methods=['GET'])
def get_user_progress(user_id):
    """Get user's quiz progress
    ---
    tags:
      - Admin
    summary: Get user quiz progress
    description: Returns quiz attempts and book progress for a specific user
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
        description: User ID
    responses:
      200:
        description: User progress retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                user:
                  type: object
                progress:
                  type: object
                  properties:
                    quiz_attempts:
                      type: array
                      items:
                        type: object
                        properties:
                          id:
                            type: integer
                          book_name:
                            type: string
                          level_name:
                            type: string
                          total_questions:
                            type: integer
                          correct_answers:
                            type: integer
                          score_percentage:
                            type: number
                          status:
                            type: string
                          started_at:
                            type: string
                          completed_at:
                            type: string
                    book_progress:
                      type: array
                    total_quizzes:
                      type: integer
                    total_books_progress:
                      type: integer
      404:
        description: User not found
    """
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    progress = user_service.get_user_quiz_progress(user_id)
    
    return jsonify({
        'status': 'success',
        'data': {
            'user': user,
            'progress': progress
        }
    }), 200


@admin_users_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Activate or deactivate user
    ---
    tags:
      - Admin
    summary: Toggle user status
    description: Activate or deactivate a user account
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
        description: User ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - is_active
          properties:
            is_active:
              type: boolean
              example: true
              description: True to activate, False to deactivate
    responses:
      200:
        description: Status updated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: User activated successfully
      404:
        description: User not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: User not found
    """
    data = request.get_json()
    is_active = data.get('is_active', False)
    
    success = user_service.toggle_user_status(user_id, is_active)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': f'User {"activated" if is_active else "deactivated"} successfully'
        }), 200
    else:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

@admin_users_bp.route('/users/<int:user_id>/admin-status', methods=['POST'])
def toggle_admin_status(user_id):
    """Promote or demote a user to admin"""
    data = request.get_json()
    is_admin = data.get('is_admin', False)
    success = user_service.set_user_admin_status(user_id, is_admin)
    if success:
        return jsonify({
            'status': 'success',
            'message': f'User {"promoted to" if is_admin else "demoted from"} admin successfully'
        }), 200
    else:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404


@admin_users_bp.route('/users/stats/summary', methods=['GET'])
def get_user_stats_summary():
    """Get user statistics summary
    ---
    tags:
      - Admin
    summary: Get user statistics
    description: Returns overall statistics about all users
    responses:
      200:
        description: Statistics retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                total_users:
                  type: integer
                  example: 150
                total_quizzes:
                  type: integer
                  example: 1250
                total_questions:
                  type: integer
                  example: 50000
                total_correct:
                  type: integer
                  example: 42500
                avg_quizzes_per_user:
                  type: number
                  example: 8.3
    """
    stats = user_service.get_user_stats_summary()
    
    return jsonify({'status': 'success', 'data': stats}), 200