# app/__init__.py
from flask import Flask, request, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from flasgger.utils import swag_from
from datetime import timedelta
from dotenv import load_dotenv
import os

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Load environment variables from .env for local development
    load_dotenv()
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # OAuth Configuration
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Determine redirect URI based on environment
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER')
    if is_production:
        app.config['GOOGLE_REDIRECT_URI'] = os.environ.get('GOOGLE_REDIRECT_URI_PROD')
    else:
        app.config['GOOGLE_REDIRECT_URI'] = os.environ.get('GOOGLE_REDIRECT_URI_LOCAL')
    
    # SMTP Configuration
    app.config['SMTP_HOST'] = os.environ.get('SMTP_HOST')
    app.config['SMTP_PORT'] = int(os.environ.get('SMTP_PORT', 587))
    app.config['SMTP_USERNAME'] = os.environ.get('SMTP_USERNAME')
    app.config['SMTP_PASSWORD'] = os.environ.get('SMTP_PASSWORD')
    app.config['SMTP_FROM_EMAIL'] = os.environ.get('SMTP_FROM_EMAIL')
    app.config['SMTP_FROM_NAME'] = os.environ.get('SMTP_FROM_NAME', 'Bible Quiz App')
    
    # Admin Configuration
    app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME')
    app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD')
    app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL')
    
    # Frontend URL for CORS
    if is_production:
        frontend_url = os.environ.get('FRONTEND_URL_PROD', 'https://bibel-quiz.lovable.app')
    else:
        frontend_url = os.environ.get('FRONTEND_URL_LOCAL', 'http://localhost:3000')
    
    # Swagger configuration
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
        "title": "Bible Quiz API",
        "description": "API for Bible Quiz Application",
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
    
    # CORS Configuration
    CORS(app, 
         origins=[frontend_url, "http://localhost:3000", "http://localhost:5000", "https://*.lovable.app"],
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
         expose_headers=["Content-Type", "Authorization"])
    
    # Initialize JWT
    JWTManager(app)
    
    # Initialize Swagger
    swagger = Swagger(app, config=swagger_config)
    
    # Import OAuth
    from app.routes.auth import oauth
    
    # Configure OAuth
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    # Initialize OAuth with app
    oauth.init_app(app)
    
    # Import blueprints
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
    
    @app.route('/auth/google/login', methods=['GET'])
    def google_login_alias():
        return redirect(url_for('auth.google_login', **request.args))

    @app.route('/auth/google/callback', methods=['GET'])
    def google_callback_alias():
        return redirect(url_for('auth.google_callback', **request.args))

    print("✅ Blueprints registered successfully")
    print(f"   - Environment: {'Production' if is_production else 'Development'}")
    print(f"   - Frontend URL: {frontend_url}")
    print(f"   - Google OAuth: {'Configured' if app.config['GOOGLE_CLIENT_ID'] else 'Not configured'}")
    print("   - Auth routes: /api/auth")
    print("   - User routes: /api/users")
    print("   - Quiz routes: /api/quiz")
    print("   - Bible routes: /api/bible")
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return {
            'status': 'healthy',
            'message': 'Bible Quiz API is running',
            'version': '1.0.0',
            'environment': os.environ.get('FLASK_ENV', 'production'),
            'google_oauth': bool(app.config['GOOGLE_CLIENT_ID'])
        }, 200
    
    return app