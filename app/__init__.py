# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
# Python 3.14 Compatibility: Import swag_from directly from its submodule
from flasgger.utils import swag_from
from datetime import timedelta
import os

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Swagger configuration
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,  # all endpoints
                "model_filter": lambda tag: True,  # all models
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
        "title": "Bible Quiz API",
        "description": "API for Bible Quiz Application with User Management, Quiz Tracking, and Progress Monitoring",
        "version": "1.0.0",
        "termsOfService": "/terms",
        "contact": {
            "name": "API Support",
            "email": "support@biblequiz.com"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer {token}'"
            }
        },
        "security": [
            {
                "BearerAuth": []
            }
        ]
    }
    
    app.config['SWAGGER'] = swagger_config
    
    # Enable CORS for local development and your production Render domain
    CORS(app, origins=[
        "http://localhost:3000", 
        "http://localhost:5000",
        "https://bibel-quiz.onrender.com"  # Crucial for live API testing via Swagger UI
    ], supports_credentials=True)
    
    # Initialize JWT
    JWTManager(app)
    
    # Initialize Swagger
    swagger = Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "Bible Quiz API",
            "description": "API for Bible Quiz Application with User Management, Quiz Tracking, and Progress Monitoring",
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@biblequiz.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer {token}'"
            }
        },
        "security": [
            {
                "BearerAuth": []
            }
        ],
        "basePath": "/",
        "schemes": ["https", "http"],  # Prioritize secure HTTPS to avoid "Failed to fetch" blockages
        "tags": [
            {"name": "Authentication", "description": "User authentication endpoints"},
            {"name": "User Profile", "description": "User profile management"},
            {"name": "Quiz", "description": "Quiz management and tracking"},
            {"name": "Bible", "description": "Bible scripture endpoints"},
            {"name": "Admin", "description": "Admin center - Bible and Questions import"},
            {"name": "System", "description": "System health and status"}
        ]
    })
    
    # Import blueprints (make sure all imports are here)
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.quiz import quiz_bp
    from app.routes.bible import bible_bp
    
    # Import admin blueprint
    try:
        from admin_center_api import create_admin_blueprint
        admin_bp = create_admin_blueprint()
        app.register_blueprint(admin_bp)
        print("✅ Admin routes registered at /api/admin")
    except ImportError as e:
        print(f"⚠️ Admin API not available: {e}")
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
    app.register_blueprint(bible_bp, url_prefix='/api/bible')
    
    print("✅ Blueprints registered successfully")
    print("   - Auth routes: /api/auth")
    print("   - User routes: /api/users")
    print("   - Quiz routes: /api/quiz")
    print("   - Bible routes: /api/bible")
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint
        ---
        tags:
          - System
        responses:
          200:
            description: API is healthy
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: healthy
                message:
                  type: string
                  example: Bible Quiz API is running
                version:
                  type: string
                  example: 1.0.0
        """
        return {
            'status': 'healthy',
            'message': 'Bible Quiz API is running',
            'version': '1.0.0'
        }, 200
    
    return app