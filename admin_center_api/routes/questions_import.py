# admin_center_api/routes/questions_import.py
from flask import Blueprint, request, jsonify
from admin_center_api.services.questions_import_service import QuestionsImportService

questions_import_bp = Blueprint('questions_import', __name__)
questions_service = QuestionsImportService()

@questions_import_bp.route('/status', methods=['GET'])
def get_questions_status():
    """Get current questions import status"""
    status = questions_service.get_questions_status()
    return jsonify({
        'status': 'success',
        'data': status
    }), 200

@questions_import_bp.route('/import/json', methods=['POST'])
def import_questions_json():
    """Import questions from JSON file"""
    data = request.get_json()
    
    if not data.get('file_path') or not data.get('language'):
        return jsonify({
            'status': 'error',
            'message': 'file_path and language are required'
        }), 400
    
    result = questions_service.import_questions_json(data['file_path'], data['language'])
    
    if result['success']:
        return jsonify({'status': 'success', 'data': result}), 200
    else:
        return jsonify({'status': 'error', 'message': result['message']}), 400

@questions_import_bp.route('/import/folder', methods=['POST'])
def import_questions_folder():
    """Import all questions from a folder"""
    data = request.get_json()
    
    if not data.get('folder_path') or not data.get('language'):
        return jsonify({
            'status': 'error',
            'message': 'folder_path and language are required'
        }), 400
    
    result = questions_service.import_folder(data['folder_path'], data['language'])
    
    return jsonify({
        'status': 'success',
        'data': result
    }), 200