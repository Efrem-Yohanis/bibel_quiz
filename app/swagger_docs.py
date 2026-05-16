# app/swagger_docs.py
"""
Swagger documentation templates for API endpoints
"""

# Auth endpoints documentation
REGISTER_DOC = {
    'tags': ['Authentication'],
    'summary': 'Register a new user',
    'description': 'Create a new user account',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['username', 'password'],
                'properties': {
                    'username': {'type': 'string', 'example': 'john_doe'},
                    'email': {'type': 'string', 'example': 'john@example.com'},
                    'password': {'type': 'string', 'example': 'password123'}
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'User registered successfully',
            'examples': {
                'application/json': {
                    'success': True,
                    'message': 'User registered successfully',
                    'user': {
                        'id': 1,
                        'username': 'john_doe',
                        'email': 'john@example.com',
                        'created_at': '2024-01-01T00:00:00'
                    }
                }
            }
        },
        400: {
            'description': 'Registration failed',
            'examples': {
                'application/json': {
                    'success': False,
                    'message': 'Username already exists'
                }
            }
        }
    }
}

LOGIN_DOC = {
    'tags': ['Authentication'],
    'summary': 'Login user',
    'description': 'Authenticate user and get access token',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['username_or_email', 'password'],
                'properties': {
                    'username_or_email': {'type': 'string', 'example': 'john_doe'},
                    'password': {'type': 'string', 'example': 'password123'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Login successful',
            'examples': {
                'application/json': {
                    'success': True,
                    'access_token': 'eyJhbGciOiJIUzI1NiIs...',
                    'token_type': 'bearer',
                    'expires_at': '2024-01-31T00:00:00',
                    'user': {
                        'id': 1,
                        'username': 'john_doe'
                    }
                }
            }
        },
        401: {
            'description': 'Invalid credentials'
        }
    }
}

# User endpoints documentation
GET_PROFILE_DOC = {
    'tags': ['User'],
    'summary': 'Get user profile',
    'description': 'Get current user profile information',
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {
            'description': 'Profile retrieved successfully',
            'examples': {
                'application/json': {
                    'success': True,
                    'user': {
                        'id': 1,
                        'username': 'john_doe',
                        'email': 'john@example.com',
                        'created_at': '2024-01-01T00:00:00',
                        'total_quizzes_taken': 5,
                        'total_correct_answers': 42,
                        'total_questions_answered': 50
                    }
                }
            }
        },
        401: {
            'description': 'Unauthorized - Invalid or missing token'
        }
    }
}

GET_COMPLETE_PROFILE_DOC = {
    'tags': ['User'],
    'summary': 'Get complete user profile',
    'description': 'Get complete user profile with quiz history, progress, and statistics',
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {
            'description': 'Complete profile retrieved successfully',
            'examples': {
                'application/json': {
                    'success': True,
                    'profile': {
                        'user': {...},
                        'statistics': {...},
                        'quiz_history': [...],
                        'in_progress_quizzes': [...],
                        'book_progress': [...],
                        'recent_activity': [...]
                    }
                }
            }
        }
    }
}

# Quiz endpoints documentation
START_QUIZ_DOC = {
    'tags': ['Quiz'],
    'summary': 'Start a new quiz',
    'description': 'Create a new quiz session for a specific book',
    'security': [{'BearerAuth': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['book_name', 'total_questions'],
                'properties': {
                    'book_name': {'type': 'string', 'example': 'John'},
                    'testament': {'type': 'string', 'example': 'New'},
                    'total_questions': {'type': 'integer', 'example': 10}
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Quiz started successfully',
            'examples': {
                'application/json': {
                    'success': True,
                    'quiz': {
                        'attempt_id': 1,
                        'book_name': 'John',
                        'total_questions': 10,
                        'status': 'in_progress'
                    }
                }
            }
        }
    }
}

RESUME_QUIZ_DOC = {
    'tags': ['Quiz'],
    'summary': 'Resume an in-progress quiz',
    'description': 'Get quiz data to resume from where user stopped',
    'security': [{'BearerAuth': []}],
    'parameters': [
        {
            'name': 'attempt_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'Quiz attempt ID'
        }
    ],
    'responses': {
        200: {
            'description': 'Quiz data retrieved for resuming',
            'examples': {
                'application/json': {
                    'success': True,
                    'quiz': {
                        'attempt_id': 1,
                        'book_name': 'John',
                        'answered_questions': 5,
                        'total_questions': 10,
                        'progress_percentage': 50,
                        'previous_answers': [...],
                        'can_resume': True
                    }
                }
            }
        }
    }
}