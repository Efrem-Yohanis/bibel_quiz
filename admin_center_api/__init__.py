# admin_center_api/__init__.py
from flask import Blueprint

def create_admin_blueprint():
    """Create admin API blueprint with Swagger documentation"""
    from admin_center_api.routes.bible_import import bible_import_bp
    from admin_center_api.routes.questions_import import questions_import_bp
    
    admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
    
    # Register sub-blueprints
    admin_bp.register_blueprint(bible_import_bp, url_prefix='/bible')
    admin_bp.register_blueprint(questions_import_bp, url_prefix='/questions')
    
    # Add admin info endpoint
    @admin_bp.route('/info', methods=['GET'])
    def admin_info():
        """Get admin API information
        ---
        tags:
          - Admin
        summary: Get admin API info
        description: Returns information about available admin endpoints
        responses:
          200:
            description: Admin API information
            schema:
              type: object
              properties:
                name:
                  type: string
                  example: Admin Center API
                version:
                  type: string
                  example: 1.0.0
                endpoints:
                  type: array
        """
        return {
            'status': 'success',
            'name': 'Admin Center API',
            'version': '1.0.0',
            'endpoints': [
                'GET  /api/admin/bible/status',
                'POST /api/admin/bible/import/book',
                'POST /api/admin/bible/import/folder',
                'GET  /api/admin/questions/status',
                'POST /api/admin/questions/import/json',
                'POST /api/admin/questions/import/folder'
            ]
        }, 200
    
    return admin_bp