# admin_center_api/routes/bible_import.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from admin_center_api.services.bible_import_service import BibleImportService

bible_import_bp = Blueprint('bible_import', __name__)
bible_service = BibleImportService()


@bible_import_bp.route('/status', methods=['GET'])
def get_import_status():
    """Get current Bible import status
    ---
    tags:
      - Admin
    summary: Get Bible import status
    description: Returns information about imported Bible data including books, verses, and languages
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
                books_imported:
                  type: integer
                  example: 66
                verses_imported:
                  type: integer
                  example: 31102
                verse_texts_by_language:
                  type: object
                  example: {"en": 31102, "am": 31102, "or": 31102}
                languages_available:
                  type: array
                  example: ["en", "am", "or"]
    """
    status = bible_service.get_import_status()
    return jsonify({'status': 'success', 'data': status}), 200


@bible_import_bp.route('/import/book', methods=['POST'])
def import_book():
    """Import a single Bible book
    ---
    tags:
      - Admin
    summary: Import a single book
    description: Import a single Bible text file into the database
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
              example: /path/to/John.txt
              description: Full path to the Bible text file
            language:
              type: string
              enum: [en, am, or]
              example: en
              description: Language code
    responses:
      200:
        description: Book imported successfully
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
                verses_imported:
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
    
    result = bible_service.import_book(data['file_path'], data['language'])
    
    if result['success']:
        return jsonify({'status': 'success', 'data': result}), 200
    else:
        return jsonify({'status': 'error', 'message': result['message']}), 400


@bible_import_bp.route('/import/folder', methods=['POST'])
def import_folder():
    """Import all Bible books from a folder
    ---
    tags:
      - Admin
    summary: Import multiple books
    description: Import all Bible text files from a folder
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
              example: /path/to/bible/folder
              description: Path to folder containing Bible text files
            language:
              type: string
              enum: [en, am, or]
              example: en
    responses:
      200:
        description: Books imported successfully
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
      400:
        description: Invalid parameters
    """
    data = request.get_json()
    
    if not data.get('folder_path') or not data.get('language'):
        return jsonify({
            'status': 'error',
            'message': 'folder_path and language are required'
        }), 400
    
    result = bible_service.import_folder(data['folder_path'], data['language'])
    
    return jsonify({'status': 'success', 'data': result}), 200