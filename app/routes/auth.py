# app/routes/auth.py
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import secrets
import sysa
from pathlib import Path
from flasgger import Swagger
from flasgger.utils import swag_from
from authlib.integrations.flask_client import OAuth
from app.utils.email_service import send_email

load_dotenv()

# Create blueprint
auth_bp = Blueprint('auth', __name__)

oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Import simple auth service
try:
    from services.auth_service_simple import AuthService
    from schemas.schemas import UserCreate, UserLogin
    USE_SIMPLE_SERVICE = True
    print("✅ Using simple AuthService")
except ImportError as e:
    print(f"⚠️ Could not import AuthService: {e}")
    USE_SIMPLE_SERVICE = False

# ==================== Helper Functions ====================

def success_response(data=None, message=None):
    """Create a success response"""
    return {
        'status': 'success',
        'message': message,
        'data': data or {}
    }, 200

def error_response(message, status_code=400):
    """Create an error response"""
    return {
        'status': 'error',
        'message': message,
        'data': {}
    }, status_code


def generate_temp_password(length=12):
    return secrets.token_urlsafe(length)


def _send_registration_email(username, email, password=None, google_signup=False):
    if not email:
        return False, 'No email provided'

    if google_signup:
        subject = 'Your Bible Quiz account is ready'
        body = (
            f'Hello {username},\n\n'
            'Your account has been created using Google sign-in.\n\n'
            f'Username: {username}\n'
            f'Temporary password: {password}\n\n'
            'You can use Google authentication to sign in, or log in with this temporary password and change it later.\n\n'
            'If you did not request this, please contact support.\n\n'
            'Bible Quiz Team'
        )
    else:
        subject = 'Welcome to Bible Quiz'
        body = (
            f'Hello {username},\n\n'
            'Thank you for registering with Bible Quiz. Your account is ready.\n\n'
            f'Username: {username}\n'
            'Use the password you provided during registration to log in.\n\n'
            'If you did not create this account, please contact support.\n\n'
            'Bible Quiz Team'
        )

    return send_email(subject, body, email)

# ==================== Auth Endpoints ====================

@auth_bp.route('/health', methods=['GET'])
def health():
    """Health check for auth routes
    ---
    tags:
      - Authentication
    summary: Health check
    description: Check if authentication routes are working
    responses:
      200:
        description: Auth routes are healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: auth routes are working
            service:
              type: string
              example: simple
    """
    return jsonify({
        'status': 'auth routes are working',
        'service': 'simple' if USE_SIMPLE_SERVICE else 'fallback'
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user
    ---
    tags:
      - Authentication
    summary: Register a new user
    description: Create a new user account with username, email, and password
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              minLength: 3
              maxLength: 50
              example: john_doe
              description: Unique username
            email:
              type: string
              format: email
              example: john@example.com
              description: User email address (optional)
            password:
              type: string
              minLength: 6
              maxLength: 100
              example: password123
              description: User password
    responses:
      201:
        description: User registered successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: User registered successfully
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: john_doe
                email:
                  type: string
                  example: john@example.com
                created_at:
                  type: string
                  format: date-time
                  example: 2024-01-01T00:00:00
      400:
        description: Registration failed
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Username already exists
      500:
        description: Server error
    """
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify(error_response('Username and password are required', 400))
        
        if USE_SIMPLE_SERVICE:
            auth_service = AuthService()
            user_data = UserCreate(
                username=data['username'],
                email=data.get('email'),
                password=data['password']
            )
            user, error = auth_service.register_user(user_data)
            
            if error:
                return jsonify(error_response(error, 400))
            
            if user.email:
                sent, email_error = _send_registration_email(user.username, user.email)
                if not sent:
                    print(f"Email warning: {email_error}")
            
            return jsonify(success_response(
                data={
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'created_at': user.created_at.isoformat() if user.created_at else None
                    }
                },
                message='User registered successfully'
            ))
        else:
            # Fallback to direct database
            import sqlite3
            import hashlib
            import secrets
            
            DB_PATH = Path(__file__).parent.parent / 'bible_quiz.db'
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            def hash_password(pwd):
                salt = secrets.token_hex(16)
                pwd_hash = hashlib.sha256(f"{pwd}{salt}".encode()).hexdigest()
                return f"{salt}:{pwd_hash}"
            
            # Check if username exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (data['username'],))
            if cursor.fetchone():
                conn.close()
                return jsonify(error_response('Username already exists', 400))
            
            password_hash = hash_password(data['password'])
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (data['username'], data.get('email'), password_hash, datetime.utcnow(), datetime.utcnow()))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            if data.get('email'):
                sent, email_error = _send_registration_email(data['username'], data['email'])
                if not sent:
                    print(f"Email warning: {email_error}")

            return jsonify(success_response(
                data={
                    'user': {
                        'id': user_id,
                        'username': data['username'],
                        'email': data.get('email'),
                        'created_at': datetime.utcnow().isoformat()
                    }
                },
                message='User registered successfully'
            ))
        
    except Exception as e:
        return jsonify(error_response(f'Registration failed: {str(e)}', 500))


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return access token
    ---
    tags:
      - Authentication
    summary: Login user
    description: Authenticate user and return JWT access token
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: john_doe
              description: Username or email address
            password:
              type: string
              example: password123
              description: User password
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            access_token:
              type: string
              description: JWT access token
              example: eyJhbGciOiJIUzI1NiIs...
            token_type:
              type: string
              example: bearer
            expires_at:
              type: string
              format: date-time
              example: 2024-01-31T00:00:00
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: john_doe
      401:
        description: Invalid credentials
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Invalid credentials
      400:
        description: Missing required fields
      500:
        description: Server error
    """
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify(error_response('Username and password are required', 400))
        
        if USE_SIMPLE_SERVICE:
            auth_service = AuthService()
            login_data = UserLogin(
                username_or_email=data['username'],
                password=data['password'],
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            token_response, error = auth_service.login_user(login_data)
            
            if error:
                return jsonify(error_response(error, 401))
            
            # IMPORTANT: Convert user_id to string for JWT identity
            access_token = create_access_token(
                identity=str(token_response.user_id),  # Convert to string
                expires_delta=timedelta(days=30),
                additional_claims={
                    'username': token_response.username,
                    'is_admin': getattr(token_response, 'is_admin', False)
                }
            )
            
            return jsonify(success_response(
                data={
                    'access_token': access_token,
                    'token_type': 'bearer',
                    'expires_at': token_response.expires_at.isoformat(),
                    'user': {
                        'id': token_response.user_id,
                        'username': token_response.username
                        ,
                        'is_admin': getattr(token_response, 'is_admin', False)
                    }
                },
                message='Login successful'
            ))
        else:
            # Fallback to direct database
            import sqlite3
            import hashlib
            
            DB_PATH = Path(__file__).parent.parent / 'bible_quiz.db'
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            def verify_password(pwd, stored_hash):
                try:
                    salt, hash_value = stored_hash.split(':')
                    computed_hash = hashlib.sha256(f"{pwd}{salt}".encode()).hexdigest()
                    return computed_hash == hash_value
                except:
                    return False
            
            cursor.execute("""
              SELECT id, username, password_hash, is_active, is_admin 
                FROM users 
                WHERE username = ? OR email = ?
            """, (data['username'], data['username']))
            
            user = cursor.fetchone()
            
            if not user or not verify_password(data['password'], user['password_hash']) or not user['is_active']:
                conn.close()
                return jsonify(error_response('Invalid credentials', 401))
            
            # IMPORTANT: Convert user_id to string for JWT identity
            access_token = create_access_token(
                identity=str(user['id']),  # Convert to string
                expires_delta=timedelta(days=30),
                additional_claims={
                    'username': user['username'],
                    'is_admin': bool(user.get('is_admin', False))
                }
            )
            
            conn.close()
            
            return jsonify(success_response(
                data={
                    'access_token': access_token,
                    'token_type': 'bearer',
                    'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    'user': {
                        'id': user['id'],
                        'username': user['username']
                        ,
                        'is_admin': bool(user.get('is_admin', False))
                    }
                },
                message='Login successful'
            ))
        
    except Exception as e:
        return jsonify(error_response(f'Login failed: {str(e)}', 500))


@auth_bp.route('/google/login', methods=['GET'])
def google_login():
    """Redirect to Google for authentication
    ---
    tags:
      - Authentication
    summary: Start Google OAuth login
    description: Redirect the user to Google's OAuth consent screen for authentication
    parameters:
      - name: redirect_uri
        in: query
        type: string
        required: false
        description: The backend URL to redirect to after Google authentication. If not provided, uses the configured Google callback URL.
        example: http://localhost:8000/auth/google/callback
    responses:
      302:
        description: Redirect to Google OAuth consent screen
      400:
        description: Invalid request
    """
    redirect_uri = (
        request.args.get('redirect_uri')
        or os.environ.get('GOOGLE_REDIRECT_URI')
        or os.environ.get('GOOGLE_REDIRECT_URI_LOCAL')
        or os.environ.get('GOOGLE_REDIRECT_URI_PROD')
        or url_for('auth.google_callback', _external=True)
    )
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """Handle callback from Google OAuth
    ---
    tags:
      - Authentication
    summary: Google OAuth callback handler
    description: Process the callback from Google after user authentication. Automatically creates or links the user account and returns a JWT token.
    responses:
      200:
        description: Authentication successful
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                access_token:
                  type: string
                  description: JWT access token
                  example: eyJhbGciOiJIUzI1NiIs...
                token_type:
                  type: string
                  example: bearer
                expires_at:
                  type: string
                  format: date-time
                user:
                  type: object
                  properties:
                    id:
                      type: integer
                    username:
                      type: string
                    email:
                      type: string
                    is_admin:
                      type: boolean
      400:
        description: Google authentication failed
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
      500:
        description: Server error during authentication
    """
    try:
        token = oauth.google.authorize_access_token()
        user_info_response = oauth.google.get('userinfo')
        user_info = user_info_response.json()

        google_id = user_info.get('sub')
        email = user_info.get('email')
        username = user_info.get('name') or email.split('@')[0]

        if not google_id or not email:
            return jsonify(error_response('Google authentication failed: missing profile information', 400))

        auth_service = AuthService()
        user = auth_service.get_user_by_google_id(google_id)
        temp_password = None

        if not user:
            existing_user = auth_service.get_user_by_email(email)
            if existing_user:
                linked, error = auth_service.link_google_account(existing_user['id'], google_id)
                if not linked:
                    return jsonify(error_response(error, 400))
                user = existing_user
            else:
                new_user, temp_password, error = auth_service.create_google_user(username, email, google_id)
                if error:
                    return jsonify(error_response(error, 400))
                user = {
                    'id': new_user.id,
                    'username': new_user.username,
                    'email': new_user.email,
                    'is_admin': getattr(new_user, 'is_admin', False)
                }
                sent, email_error = _send_registration_email(username, email, password=temp_password, google_signup=True)
                if not sent:
                    print(f"Email warning: {email_error}")

        # Issue JWT for the authenticated user
        access_token = create_access_token(
            identity=str(user['id']),
            expires_delta=timedelta(days=30),
            additional_claims={
                'username': user['username'],
                'is_admin': bool(user.get('is_admin', False))
            }
        )

        response_data = {
            'access_token': access_token,
            'token_type': 'bearer',
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email'),
                'is_admin': bool(user.get('is_admin', False))
            }
        }

        redirect_uri = request.args.get('redirect_uri')
        if redirect_uri:
            return redirect(f"{redirect_uri}?access_token={access_token}&token_type=bearer")

        return jsonify(success_response(data=response_data, message='Google login successful'))
    except Exception as e:
        return jsonify(error_response(f'Google login failed: {str(e)}', 500))


@auth_bp.route('/password-reset/request', methods=['POST'])
def request_password_reset():
    """Request a password reset email
    ---
    tags:
      - Authentication
    summary: Request password reset
    description: Send a password reset link to the user's registered email address
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              format: email
              example: user@example.com
              description: User's registered email address
    responses:
      200:
        description: Password reset email sent successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Password reset email sent
      400:
        description: Email not registered or missing
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
      500:
        description: Failed to send email
    """
    try:
        data = request.get_json()
        email = data.get('email') if data else None
        if not email:
            return jsonify(error_response('Email is required', 400))

        auth_service = AuthService()
        reset_token, error = auth_service.set_password_reset_token(email)
        if error:
            return jsonify(error_response(error, 400))

        reset_url = os.environ.get('PASSWORD_RESET_URL') or ''
        if reset_url:
            reset_url = f"{reset_url}?reset_token={reset_token}"

        subject = 'Bible Quiz Password Reset'
        body = (
            f'Hello,\n\n'
            'We received a request to reset your password.\n\n'
            f'Reset token: {reset_token}\n'
            f'Alternatively, visit: {reset_url}\n\n'
            'This token expires in one hour.\n\n'
            'If you did not request a password reset, please ignore this email.\n\n'
            'Bible Quiz Team'
        )

        sent, email_error = send_email(subject, body, email)
        if not sent:
            return jsonify(error_response(f'Failed to send reset email: {email_error}', 500))

        return jsonify(success_response(message='Password reset email sent'))
    except Exception as e:
        return jsonify(error_response(f'Password reset request failed: {str(e)}', 500))


@auth_bp.route('/password-reset/confirm', methods=['POST'])
def confirm_password_reset():
    """Confirm password reset and set new password
    ---
    tags:
      - Authentication
    summary: Reset password
    description: Reset the user's password using a valid reset token
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - reset_token
            - new_password
          properties:
            reset_token:
              type: string
              example: abcdef123456789...
              description: Reset token received in password reset email
            new_password:
              type: string
              minLength: 6
              example: NewPassword123!
              description: New password (minimum 6 characters)
    responses:
      200:
        description: Password reset successful
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Password has been reset successfully
      400:
        description: Invalid token, expired token, or weak password
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
      500:
        description: Server error during password reset
    """
    try:
        data = request.get_json()
        reset_token = data.get('reset_token') if data else None
        new_password = data.get('new_password') if data else None
        if not reset_token or not new_password:
            return jsonify(error_response('Reset token and new password are required', 400))
        if len(new_password) < 6:
            return jsonify(error_response('New password must be at least 6 characters', 400))

        auth_service = AuthService()
        success, error = auth_service.reset_password(reset_token, new_password)
        if not success:
            return jsonify(error_response(error, 400))

        return jsonify(success_response(message='Password has been reset successfully'))
    except Exception as e:
        return jsonify(error_response(f'Password reset failed: {str(e)}', 500))


@auth_bp.route('/validate', methods=['GET'])
@jwt_required()
def validate_token():
    """Validate JWT token
    ---
    tags:
      - Authentication
    summary: Validate token
    description: Check if the provided JWT token is valid and not expired
    security:
      - BearerAuth: []
    responses:
      200:
        description: Token is valid
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            valid:
              type: boolean
              example: true
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
      401:
        description: Invalid or expired token
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            valid:
              type: boolean
              example: false
            message:
              type: string
    """
    try:
        user_id = get_jwt_identity()
        return jsonify({
            'status': 'success',
            'valid': True,
            'user': {'id': int(user_id) if user_id else None}
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'valid': False,
            'message': str(e)
        }), 401


@auth_bp.route('/logout', methods=['POST'])
@jwt_required(optional=True)
def logout():
    """Logout user
    ---
    tags:
      - Authentication
    summary: Logout user
    description: Invalidate the current session (client should discard the token)
    security:
      - BearerAuth: []
    responses:
      200:
        description: Logged out successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Logged out successfully
    """
    try:
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """Refresh access token"""
    try:
        user_id = get_jwt_identity()
        
        # Use SQLAlchemy instead of SQLite
        from app.database import get_db
        from app.models import User
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        username = user.username if user else 'user'
        is_admin = user.is_admin if user else False
        
        # Create new token
        access_token = create_access_token(
            identity=str(user_id),
            expires_delta=timedelta(days=30),
            additional_claims={
                'username': username,
                'is_admin': is_admin
            }
        )
        
        return jsonify({
            'status': 'success',
            'access_token': access_token,
            'token_type': 'bearer',
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 401

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password
    ---
    tags:
      - Authentication
    summary: Change password
    description: Change the authenticated user's password
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - old_password
            - new_password
          properties:
            old_password:
              type: string
              example: oldpass123
            new_password:
              type: string
              minLength: 6
              example: newpass123
    responses:
      200:
        description: Password changed successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Password changed successfully
      400:
        description: Invalid old password or weak new password
      401:
        description: Unauthorized
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('old_password') or not data.get('new_password'):
            return jsonify(error_response('Old password and new password are required', 400))
        
        if len(data['new_password']) < 6:
            return jsonify(error_response('New password must be at least 6 characters', 400))
        
        import sqlite3
        import hashlib
        
        DB_PATH = Path(__file__).parent.parent / 'bible_quiz.db'
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        def verify_password(pwd, stored_hash):
            try:
                salt, hash_value = stored_hash.split(':')
                computed_hash = hashlib.sha256(f"{pwd}{salt}".encode()).hexdigest()
                return computed_hash == hash_value
            except:
                return False
        
        def hash_password(pwd):
            import secrets
            salt = secrets.token_hex(16)
            pwd_hash = hashlib.sha256(f"{pwd}{salt}".encode()).hexdigest()
            return f"{salt}:{pwd_hash}"
        
        # Get current password hash
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user or not verify_password(data['old_password'], user[0]):
            conn.close()
            return jsonify(error_response('Invalid old password', 400))
        
        # Update password
        new_hash = hash_password(data['new_password'])
        cursor.execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?", 
                      (new_hash, datetime.utcnow(), user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify(success_response(message='Password changed successfully'))
        
    except Exception as e:
        return jsonify(error_response(f'Password change failed: {str(e)}', 500))

