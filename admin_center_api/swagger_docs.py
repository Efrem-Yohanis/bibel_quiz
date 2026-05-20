# admin_center_api/swagger_docs.py
"""
Swagger documentation for Admin Center API
"""

# ==================== User Management ====================

GET_ALL_USERS_DOC = {
    'tags': ['Admin - Users'],
    'summary': 'Get all registered users',
    'description': 'Returns a paginated list of all users with their details',
    'parameters': [
        {
            'name': 'limit',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 100,
            'description': 'Number of users to return'
        },
        {
            'name': 'offset',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 0,
            'description': 'Number of users to skip'
        }
    ],
    'responses': {
        200: {
            'description': 'List of users retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'users': {'type': 'array'},
                            'total': {'type': 'integer'},
                            'limit': {'type': 'integer'},
                            'offset': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
}

GET_USER_DETAILS_DOC = {
    'tags': ['Admin - Users'],
    'summary': 'Get user by ID',
    'description': 'Returns detailed information about a specific user',
    'parameters': [
        {
            'name': 'user_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'User ID'
        }
    ],
    'responses': {
        200: {
            'description': 'User details retrieved',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'data': {'type': 'object'}
                }
            }
        },
        404: {
            'description': 'User not found'
        }
    }
}

GET_USER_PROGRESS_DOC = {
    'tags': ['Admin - Users'],
    'summary': 'Get user quiz progress',
    'description': 'Returns quiz attempts and book progress for a specific user',
    'parameters': [
        {
            'name': 'user_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'User ID'
        }
    ],
    'responses': {
        200: {
            'description': 'User progress retrieved',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'user': {'type': 'object'},
                            'progress': {
                                'type': 'object',
                                'properties': {
                                    'quiz_attempts': {'type': 'array'},
                                    'book_progress': {'type': 'array'},
                                    'total_quizzes': {'type': 'integer'},
                                    'total_books_progress': {'type': 'integer'}
                                }
                            }
                        }
                    }
                }
            }
        },
        404: {
            'description': 'User not found'
        }
    }
}

TOGGLE_USER_STATUS_DOC = {
    'tags': ['Admin - Users'],
    'summary': 'Activate or deactivate user',
    'description': 'Toggle user active status',
    'parameters': [
        {
            'name': 'user_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'User ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'is_active': {
                        'type': 'boolean',
                        'example': True,
                        'description': 'True to activate, False to deactivate'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Status updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'message': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'User not found'
        }
    }
}

GET_USER_STATS_SUMMARY_DOC = {
    'tags': ['Admin - Users'],
    'summary': 'Get user statistics summary',
    'description': 'Returns overall statistics about all users',
    'responses': {
        200: {
            'description': 'Statistics retrieved',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'total_users': {'type': 'integer'},
                            'total_quizzes': {'type': 'integer'},
                            'total_questions': {'type': 'integer'},
                            'total_correct': {'type': 'integer'},
                            'avg_quizzes_per_user': {'type': 'number'}
                        }
                    }
                }
            }
        }
    }
}


# ==================== Language Management ====================

GET_ALL_LANGUAGES_DOC = {
    'tags': ['Admin - Languages'],
    'summary': 'Get all languages',
    'description': 'Returns list of all languages with their details',
    'responses': {
        200: {
            'description': 'Languages retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'data': {'type': 'array'}
                }
            }
        }
    }
}

ADD_LANGUAGE_DOC = {
    'tags': ['Admin - Languages'],
    'summary': 'Add a new language',
    'description': 'Creates a new language entry',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['code', 'name'],
                'properties': {
                    'code': {
                        'type': 'string',
                        'example': 'fr',
                        'description': 'Language code (2-3 letters)'
                    },
                    'name': {
                        'type': 'string',
                        'example': 'French',
                        'description': 'Language name in English'
                    },
                    'native_name': {
                        'type': 'string',
                        'example': 'Français',
                        'description': 'Native name of the language'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Language added successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'success': {'type': 'boolean'},
                            'language_id': {'type': 'integer'},
                            'message': {'type': 'string'}
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Missing required fields or duplicate code'
        }
    }
}

UPDATE_LANGUAGE_DOC = {
    'tags': ['Admin - Languages'],
    'summary': 'Update language',
    'description': 'Updates an existing language',
    'parameters': [
        {
            'name': 'language_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'Language ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'string', 'example': 'fr'},
                    'name': {'type': 'string', 'example': 'French'},
                    'native_name': {'type': 'string', 'example': 'Français'},
                    'is_active': {'type': 'boolean', 'example': True}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Language updated successfully'
        },
        400: {
            'description': 'Update failed'
        }
    }
}

DELETE_LANGUAGE_DOC = {
    'tags': ['Admin - Languages'],
    'summary': 'Delete language',
    'description': 'Deletes a language (only if not in use)',
    'parameters': [
        {
            'name': 'language_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'Language ID'
        }
    ],
    'responses': {
        200: {
            'description': 'Language deleted successfully'
        },
        400: {
            'description': 'Cannot delete - language in use'
        },
        404: {
            'description': 'Language not found'
        }
    }
}


# ==================== Book Management ====================

GET_ALL_BOOKS_DOC = {
    'tags': ['Admin - Books'],
    'summary': 'Get all books',
    'description': 'Returns list of all books, optionally filtered by testament',
    'parameters': [
        {
            'name': 'testament',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['Old', 'New'],
            'description': 'Filter by testament'
        }
    ],
    'responses': {
        200: {
            'description': 'Books retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'data': {'type': 'array'}
                }
            }
        }
    }
}

GET_BOOK_DETAILS_DOC = {
    'tags': ['Admin - Books'],
    'summary': 'Get book by ID',
    'description': 'Returns detailed information about a specific book',
    'parameters': [
        {
            'name': 'book_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'Book ID'
        }
    ],
    'responses': {
        200: {
            'description': 'Book details retrieved'
        },
        404: {
            'description': 'Book not found'
        }
    }
}

ADD_BOOK_DOC = {
    'tags': ['Admin - Books'],
    'summary': 'Add a new book',
    'description': 'Creates a new book entry',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['name', 'testament'],
                'properties': {
                    'name': {
                        'type': 'string',
                        'example': 'Genesis',
                        'description': 'Book name'
                    },
                    'testament': {
                        'type': 'string',
                        'enum': ['Old', 'New'],
                        'example': 'Old',
                        'description': 'Testament name'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Book added successfully'
        },
        400: {
            'description': 'Missing required fields or book already exists'
        }
    }
}

UPDATE_BOOK_DOC = {
    'tags': ['Admin - Books'],
    'summary': 'Update book',
    'description': 'Updates an existing book',
    'parameters': [
        {
            'name': 'book_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'Book ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'example': 'Genesis'},
                    'testament': {'type': 'string', 'enum': ['Old', 'New']}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Book updated successfully'
        },
        400: {
            'description': 'Update failed'
        },
        404: {
            'description': 'Book not found'
        }
    }
}

DELETE_BOOK_DOC = {
    'tags': ['Admin - Books'],
    'summary': 'Delete book',
    'description': 'Deletes a book (only if no questions associated)',
    'parameters': [
        {
            'name': 'book_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'Book ID'
        }
    ],
    'responses': {
        200: {
            'description': 'Book deleted successfully'
        },
        400: {
            'description': 'Cannot delete - book has questions'
        },
        404: {
            'description': 'Book not found'
        }
    }
}


# ==================== Bible Import ====================

BIBLE_IMPORT_STATUS_DOC = {
    'tags': ['Admin - Bible Import'],
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
    'tags': ['Admin - Bible Import'],
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

BIBLE_IMPORT_FOLDER_DOC = {
    'tags': ['Admin - Bible Import'],
    'summary': 'Import multiple Bible books',
    'description': 'Import all Bible text files from a folder',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['folder_path', 'language'],
                'properties': {
                    'folder_path': {'type': 'string', 'example': '/path/to/bible/folder'},
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


# ==================== Questions Import ====================

QUESTIONS_IMPORT_STATUS_DOC = {
    'tags': ['Admin - Questions Import'],
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
    'tags': ['Admin - Questions Import'],
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

QUESTIONS_IMPORT_FOLDER_DOC = {
    'tags': ['Admin - Questions Import'],
    'summary': 'Import multiple question files',
    'description': 'Import all quiz question JSON files from a folder',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['folder_path', 'language'],
                'properties': {
                    'folder_path': {'type': 'string', 'example': '/path/to/questions/folder'},
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