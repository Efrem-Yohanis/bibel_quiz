# admin_center_api/routes/admin_languages.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from admin_center_api.services.language_management_service import LanguageManagementService

admin_languages_bp = Blueprint('admin_languages', __name__)
language_service = LanguageManagementService()


@admin_languages_bp.route('/languages', methods=['GET'])
def get_all_languages():
    """Get all languages
    ---
    tags:
      - Admin
    summary: Get all languages
    description: Returns list of all languages with their details
    responses:
      200:
        description: Languages retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  code:
                    type: string
                    example: en
                  name:
                    type: string
                    example: English
                  native_name:
                    type: string
                    example: English
                  is_active:
                    type: boolean
                    example: true
                  created_at:
                    type: string
    """
    languages = language_service.get_all_languages()
    
    return jsonify({'status': 'success', 'data': languages}), 200


@admin_languages_bp.route('/languages', methods=['POST'])
def add_language():
    """Add a new language
    ---
    tags:
      - Admin
    summary: Add new language
    description: Creates a new language entry
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - code
            - name
          properties:
            code:
              type: string
              example: fr
              description: Language code (2-3 letters)
            name:
              type: string
              example: French
              description: Language name in English
            native_name:
              type: string
              example: Français
              description: Native name of the language
    responses:
      201:
        description: Language added successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                success:
                  type: boolean
                language_id:
                  type: integer
                message:
                  type: string
      400:
        description: Missing required fields or duplicate code
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
    
    if not data.get('code') or not data.get('name'):
        return jsonify({'status': 'error', 'message': 'code and name are required'}), 400
    
    result = language_service.add_language(
        code=data['code'],
        name=data['name'],
        native_name=data.get('native_name', '')
    )
    
    if result['success']:
        return jsonify({'status': 'success', 'data': result}), 201
    else:
        return jsonify({'status': 'error', 'message': result['message']}), 400


@admin_languages_bp.route('/languages/<int:language_id>', methods=['PUT'])
def update_language(language_id):
    """Update language
    ---
    tags:
      - Admin
    summary: Update language
    description: Updates an existing language
    parameters:
      - name: language_id
        in: path
        required: true
        type: integer
        description: Language ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            code:
              type: string
              example: fr
            name:
              type: string
              example: French
            native_name:
              type: string
              example: Français
            is_active:
              type: boolean
              example: true
    responses:
      200:
        description: Language updated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
      400:
        description: Update failed
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
      404:
        description: Language not found
    """
    data = request.get_json()
    
    result = language_service.update_language(
        language_id=language_id,
        code=data.get('code'),
        name=data.get('name'),
        native_name=data.get('native_name'),
        is_active=data.get('is_active')
    )
    
    if result['success']:
        return jsonify({'status': 'success', 'message': result['message']}), 200
    else:
        return jsonify({'status': 'error', 'message': result['message']}), 400


@admin_languages_bp.route('/languages/<int:language_id>', methods=['DELETE'])
def delete_language(language_id):
    """Delete language
    ---
    tags:
      - Admin
    summary: Delete language
    description: Deletes a language (only if not in use)
    parameters:
      - name: language_id
        in: path
        required: true
        type: integer
        description: Language ID
    responses:
      200:
        description: Language deleted successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
      400:
        description: Cannot delete - language in use
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
      404:
        description: Language not found
    """
    result = language_service.delete_language(language_id)
    
    if result['success']:
        return jsonify({'status': 'success', 'message': result['message']}), 200
    else:
        return jsonify({'status': 'error', 'message': result['message']}), 400