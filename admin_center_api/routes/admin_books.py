# admin_center_api/routes/admin_books.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from admin_center_api.services.book_management_service import BookManagementService

admin_books_bp = Blueprint('admin_books', __name__)
book_service = BookManagementService()


@admin_books_bp.route('/books', methods=['GET'])
def get_all_books():
    """Get all books
    ---
    tags:
      - Admin
    summary: Get all books
    description: Returns list of all books, optionally filtered by testament
    parameters:
      - name: testament
        in: query
        type: string
        required: false
        enum: ['Old', 'New']
        description: Filter by testament
    responses:
      200:
        description: Books retrieved successfully
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
                  name:
                    type: string
                  testament:
                    type: string
                  chapters:
                    type: integer
                  verses:
                    type: integer
    """
    testament = request.args.get('testament')
    
    books = book_service.get_all_books(testament)
    
    return jsonify({'status': 'success', 'data': books}), 200


@admin_books_bp.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Get book by ID
    ---
    tags:
      - Admin
    summary: Get book details
    description: Returns detailed information about a specific book
    parameters:
      - name: book_id
        in: path
        required: true
        type: integer
        description: Book ID
    responses:
      200:
        description: Book details retrieved successfully
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
                name:
                  type: string
                testament:
                  type: string
                chapters:
                  type: integer
                verses:
                  type: integer
      404:
        description: Book not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Book not found
    """
    book = book_service.get_book_by_id(book_id)
    
    if not book:
        return jsonify({'status': 'error', 'message': 'Book not found'}), 404
    
    return jsonify({'status': 'success', 'data': book}), 200


@admin_books_bp.route('/books', methods=['POST'])
def add_book():
    """Add a new book
    ---
    tags:
      - Admin
    summary: Add new book
    description: Creates a new book entry
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - testament
          properties:
            name:
              type: string
              example: Genesis
              description: Book name
            testament:
              type: string
              enum: ['Old', 'New']
              example: Old
              description: Testament name
    responses:
      201:
        description: Book added successfully
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
                book_id:
                  type: integer
                message:
                  type: string
      400:
        description: Missing required fields or book already exists
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
    
    if not data.get('name') or not data.get('testament'):
        return jsonify({'status': 'error', 'message': 'name and testament are required'}), 400
    
    result = book_service.add_book(data['name'], data['testament'])
    
    if result['success']:
        return jsonify({'status': 'success', 'data': result}), 201
    else:
        return jsonify({'status': 'error', 'message': result['message']}), 400


@admin_books_bp.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Update book
    ---
    tags:
      - Admin
    summary: Update book
    description: Updates an existing book
    parameters:
      - name: book_id
        in: path
        required: true
        type: integer
        description: Book ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Genesis
            testament:
              type: string
              enum: ['Old', 'New']
    responses:
      200:
        description: Book updated successfully
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
      404:
        description: Book not found
    """
    data = request.get_json()
    
    result = book_service.update_book(
        book_id=book_id,
        name=data.get('name'),
        testament=data.get('testament')
    )
    
    if result['success']:
        return jsonify({'status': 'success', 'message': result['message']}), 200
    else:
        return jsonify({'status': 'error', 'message': result['message']}), 400


@admin_books_bp.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete book
    ---
    tags:
      - Admin
    summary: Delete book
    description: Deletes a book (only if no questions associated)
    parameters:
      - name: book_id
        in: path
        required: true
        type: integer
        description: Book ID
    responses:
      200:
        description: Book deleted successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
      400:
        description: Cannot delete - book has questions
      404:
        description: Book not found
    """
    result = book_service.delete_book(book_id)
    
    if result['success']:
        return jsonify({'status': 'success', 'message': result['message']}), 200
    else:
        return jsonify({'status': 'error', 'message': result['message']}), 400