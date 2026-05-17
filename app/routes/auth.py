# app/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
import sys
from pathlib import Path
from flasgger import Swagger
from flasgger.utils import swag_from
# Create blueprint
auth_bp = Blueprint('auth', __name__)

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
                additional_claims={'username': token_response.username}
            )
            
            return jsonify(success_response(
                data={
                    'access_token': access_token,
                    'token_type': 'bearer',
                    'expires_at': token_response.expires_at.isoformat(),
                    'user': {
                        'id': token_response.user_id,
                        'username': token_response.username
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
                SELECT id, username, password_hash, is_active 
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
                additional_claims={'username': user['username']}
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
                    }
                },
                message='Login successful'
            ))
        
    except Exception as e:
        return jsonify(error_response(f'Login failed: {str(e)}', 500))


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
    """Refresh access token
    ---
    tags:
      - Authentication
    summary: Refresh access token
    description: Get a new access token using the current valid token
    security:
      - BearerAuth: []
    responses:
      200:
        description: Token refreshed successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            access_token:
              type: string
              example: eyJhbGciOiJIUzI1NiIs...
            token_type:
              type: string
              example: bearer
            expires_at:
              type: string
              format: date-time
      401:
        description: Invalid or expired token
    """
    try:
        user_id = get_jwt_identity()
        
        # Get user info
        import sqlite3
        DB_PATH = Path(__file__).parent.parent / 'bible_quiz.db'
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        username = user[0] if user else 'user'
        
        # Create new token with string identity
        access_token = create_access_token(
            identity=str(user_id),  # Convert to string
            expires_delta=timedelta(days=30),
            additional_claims={'username': username}
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

