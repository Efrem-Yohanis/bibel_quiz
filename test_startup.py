#!/usr/bin/env python3
import sqlite3
from pathlib import Path
import os

# Test database
db_path = Path('app') / 'bible_quiz.db'
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        print('✅ Database tables exist')
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f'✅ Users in database: {user_count}')
        cursor.execute("SELECT id, username, is_admin FROM users WHERE is_admin=1")
        admins = cursor.fetchall()
        if admins:
            print(f'✅ Admin users found: {len(admins)}')
            for admin in admins:
                print(f'   - ID: {admin[0]}, Username: {admin[1]}, is_admin: {admin[2]}')
    conn.close()
else:
    print('⚠️ Database does not exist yet - will be created on first app startup')

# Test environment variables
print('\n📋 Environment Variables Status:')
required_vars = [
    'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 
    'GOOGLE_REDIRECT_URI_LOCAL', 'GOOGLE_REDIRECT_URI_PROD',
    'SMTP_HOST', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'SMTP_FROM_EMAIL',
    'ADMIN_USERNAME', 'ADMIN_PASSWORD', 'ADMIN_EMAIL'
]

from dotenv import load_dotenv
load_dotenv()

for var in required_vars:
    value = os.getenv(var)
    if value:
        display = value[:10] + '...' if len(str(value)) > 10 else value
        print(f'  ✅ {var}: {display}')
    else:
        print(f'  ❌ {var}: NOT SET')

# Test app creation
print('\n🚀 App Startup Test:')
try:
    from app import create_app
    app = create_app()
    print('✅ App created successfully')
    
    # Count routes
    auth_routes = [str(rule) for rule in app.url_map.iter_rules() if 'auth' in str(rule) and '/api/' in str(rule)]
    print(f'✅ Auth endpoints registered: {len(auth_routes)}')
    for route in sorted(auth_routes):
        print(f'   - {route}')
except Exception as e:
    print(f'❌ Error creating app: {e}')
    import traceback
    traceback.print_exc()
