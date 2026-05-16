# app/services/__init__.py
"""
Services package for Bible Quiz application
Simple versions without SQLAlchemy for Python 3.14 compatibility
"""

# Don't import SQLAlchemy-based services here
# Just define what's available

__all__ = []

# Try to import simple services only
try:
    from services.user_profile_service import UserProfileService
    __all__.append('UserProfileService')
    print("✅ UserProfileService loaded")
except ImportError as e:
    print(f"⚠️ UserProfileService not available: {e}")

try:
    from services.auth_service_simple import AuthService
    __all__.append('AuthService')
    print("✅ AuthService loaded")
except ImportError as e:
    print(f"⚠️ AuthService not available: {e}")