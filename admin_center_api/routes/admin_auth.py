# admin_center_api/routes/admin_auth.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt

admin_auth_bp = Blueprint('admin_auth', __name__)

@admin_auth_bp.route('/check', methods=['GET'])
@jwt_required()
def check_admin():
    """Check that current token belongs to an admin user"""
    claims = get_jwt()
    return jsonify({
        'status': 'success',
        'message': 'Admin token is valid',
        'is_admin': claims.get('is_admin', False)
    }), 200
