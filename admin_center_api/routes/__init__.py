# admin_center_api/__init__.py
from flask import Blueprint

def create_admin_blueprint():
    """Create admin API blueprint"""
    from admin_center_api.routes.bible_import import bible_import_bp
    from admin_center_api.routes.questions_import import questions_import_bp
    
    admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
    
    # Register sub-blueprints
    admin_bp.register_blueprint(bible_import_bp, url_prefix='/bible')
    admin_bp.register_blueprint(questions_import_bp, url_prefix='/questions')
    
    return admin_bp