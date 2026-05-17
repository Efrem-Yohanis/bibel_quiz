# admin_center_api/routes/questions_import.py
from flask import Blueprint, request, jsonify
from admin_center_api.services.questions_import_service import QuestionsImportService
from flasgger import Swagger
from flasgger.utils import swag_from
questions_import_bp = Blueprint('questions_import', __name__)
questions_service = QuestionsImportService()

@questions_import_bp.route('/status', methods=['GET'])
def get_questions_status():
    """Get current questions import status
    ---
    tags:
      - Admin
    summary: Get questions import status
    description: Returns information about what quiz questions have been imported
    responses:
      200:
        description: Status retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                total_questions:
                  type: integer
                  example: 500
                questions_by_language:
                  type: object
                  example: {"en": 500, "am": 500, "or": 500}
    """
    status = questions_service.get_questions_status()
    return jsonify({
        'status': 'success',
        'data': status
    }), 200

@questions_import_bp.route('/import/json', methods=['POST'])
def import_questions_json():
    """Import questions from JSON file
    ---
    tags:
      - Admin
    summary: Import questions from JSON
    description: Import quiz questions from a JSON file
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - file_path
            - language
          properties:
            file_path:
              type: string
              example: /path/to/questions_John.json
              description: Path to the JSON file containing questions
            language:
              type: string
              enum: [en, am, or]
              example: en
    responses:
      200:
        description: Questions imported successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                book_name:
                  type: string
                questions_imported:
                  type: integer
                language:
                  type: string
      400:
        description: Import failed
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
    """
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
    """Import questions from a folder
    ---
    tags:
      - Admin
    summary: Import multiple question files
    description: Import all quiz question JSON files from a folder
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - folder_path
            - language
          properties:
            folder_path:
              type: string
              example: /path/to/questions/folder
              description: Path to folder containing JSON files
            language:
              type: string
              enum: [en, am, or]
              example: en
    responses:
      200:
        description: Questions imported successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                total_files:
                  type: integer
                imported:
                  type: array
                failed:
                  type: array
    """
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