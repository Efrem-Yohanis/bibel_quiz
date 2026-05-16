# admin_center_api/swagger_docs.py
"""
Swagger documentation for Admin Center API
"""

BIBLE_IMPORT_STATUS_DOC = {
    'tags': ['Admin'],
    'summary': 'Get Bible import status',
    'description': 'Returns information about imported Bible data including books, verses, and languages',
    'responses': {
        200: {
            'description': 'Success',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'books_imported': {'type': 'integer', 'example': 66},
                            'verses_imported': {'type': 'integer', 'example': 31102},
                            'verse_texts_by_language': {'type': 'object'},
                            'languages_available': {'type': 'array'}
                        }
                    }
                }
            }
        }
    }
}

BIBLE_IMPORT_BOOK_DOC = {
    'tags': ['Admin'],
    'summary': 'Import a single Bible book',
    'description': 'Import one Bible text file into the database',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['file_path', 'language'],
                'properties': {
                    'file_path': {'type': 'string', 'example': '/path/to/John.txt'},
                    'language': {'type': 'string', 'enum': ['en', 'am', 'or'], 'example': 'en'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Import successful'},
        400: {'description': 'Invalid parameters'}
    }
}

QUESTIONS_IMPORT_STATUS_DOC = {
    'tags': ['Admin'],
    'summary': 'Get questions import status',
    'description': 'Returns information about imported quiz questions',
    'responses': {
        200: {
            'description': 'Success',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'total_questions': {'type': 'integer', 'example': 500},
                            'questions_by_language': {'type': 'object'}
                        }
                    }
                }
            }
        }
    }
}

QUESTIONS_IMPORT_JSON_DOC = {
    'tags': ['Admin'],
    'summary': 'Import questions from JSON',
    'description': 'Import quiz questions from a JSON file',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['file_path', 'language'],
                'properties': {
                    'file_path': {'type': 'string', 'example': '/path/to/questions_John.json'},
                    'language': {'type': 'string', 'enum': ['en', 'am', 'or'], 'example': 'en'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Import successful'},
        400: {'description': 'Invalid parameters'}
    }
}