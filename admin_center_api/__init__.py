# admin_center_api/__init__.py
from flask import Blueprint, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

from flasgger import swag_from

def create_admin_blueprint():
    """Create admin API blueprint with all routes"""
    from admin_center_api.routes.bible_import import bible_import_bp
    from admin_center_api.routes.questions_import import questions_import_bp
    from admin_center_api.routes.admin_users import admin_users_bp
    from admin_center_api.routes.admin_languages import admin_languages_bp
    from admin_center_api.routes.admin_books import admin_books_bp
    from admin_center_api.routes.admin_auth import admin_auth_bp
    
    admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

    @admin_bp.before_request
    def require_admin():
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims.get('is_admin'):
                return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 401
    
    # Register sub-blueprints
    admin_bp.register_blueprint(bible_import_bp, url_prefix='/bible')
    admin_bp.register_blueprint(questions_import_bp, url_prefix='/questions')
    admin_bp.register_blueprint(admin_users_bp, url_prefix='/users')
    admin_bp.register_blueprint(admin_languages_bp, url_prefix='/languages')
    admin_bp.register_blueprint(admin_books_bp, url_prefix='/books')
    admin_bp.register_blueprint(admin_auth_bp, url_prefix='/auth')
    
    # Admin info endpoint
    @admin_bp.route('/info', methods=['GET'])
    def admin_info():
        """Get admin API information
        ---
        tags:
          - Admin
        summary: Get admin API information
        description: Returns information about all available admin endpoints
        responses:
          200:
            description: Admin API information retrieved successfully
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                name:
                  type: string
                  example: Admin Center API
                version:
                  type: string
                  example: 1.0.0
                endpoints:
                  type: object
                  properties:
                    bible_import:
                      type: array
                      items:
                        type: string
                    questions_import:
                      type: array
                      items:
                        type: string
                    user_management:
                      type: array
                      items:
                        type: string
                    language_management:
                      type: array
                      items:
                        type: string
                    book_management:
                      type: array
                      items:
                        type: string
        """
        return {
            'status': 'success',
            'name': 'Admin Center API',
            'version': '1.0.0',
            'endpoints': {
                'bible_import': [
                    'GET  /api/admin/bible/status',
                    'POST /api/admin/bible/import/book',
                    'POST /api/admin/bible/import/folder'
                ],
                'questions_import': [
                    'GET  /api/admin/questions/status',
                    'POST /api/admin/questions/import/json',
                    'POST /api/admin/questions/import/folder'
                ],
                'user_management': [
                    'GET    /api/admin/users',
                    'GET    /api/admin/users/{id}',
                    'GET    /api/admin/users/{id}/progress',
                    'POST   /api/admin/users/{id}/toggle-status',
                    'GET    /api/admin/users/stats/summary'
                ],
                'language_management': [
                    'GET    /api/admin/languages',
                    'POST   /api/admin/languages',
                    'PUT    /api/admin/languages/{id}',
                    'DELETE /api/admin/languages/{id}'
                ],
                'book_management': [
                    'GET    /api/admin/books',
                    'GET    /api/admin/books/{id}',
                    'POST   /api/admin/books',
                    'PUT    /api/admin/books/{id}',
                    'DELETE /api/admin/books/{id}'
                ]
            }
        }, 200
    
    return admin_bp