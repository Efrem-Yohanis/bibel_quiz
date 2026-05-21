# run.py
"""
Bible Quiz API Server
Run: python run.py [options]

Options:
  --host HOST     Host to bind to (default: 0.0.0.0)
  --port PORT     Port to bind to (default: 5000)
  --debug         Run in debug mode
  --init-db       Initialize database before starting
  --migrate       Run database migration before starting
  --reset-db      Reset database (WARNING: deletes all data!)
"""

import os
import sys
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import test_connection, init_db, engine, Base
from sqlalchemy import text

def print_banner():
    """Print application banner"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   📖 BIBLE QUIZ API SERVER 📖                            ║
    ║                                                          ║
    ║   Version: 1.0.0                                        ║
    ║   Author: Bible Quiz Team                                ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

def check_environment():
    """Check environment configuration"""
    print("\n" + "="*60)
    print("🔍 ENVIRONMENT CHECK")
    print("="*60)
    
    IS_RENDER = os.environ.get('RENDER') or os.environ.get('DATABASE_URL')
    
    print(f"🌍 Platform: {'Render Production' if IS_RENDER else 'Local Development'}")
    print(f"🐍 Python: {sys.version}")
    
    # Check database
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url:
        db_type = 'PostgreSQL' if 'postgres' in database_url.lower() else 'SQLite'
        print(f"🗄️  Database: {db_type}")
        if 'postgres' in database_url.lower():
            # Show database host (hide credentials)
            host_part = database_url.split('@')[1].split('/')[0] if '@' in database_url else 'unknown'
            print(f"   Host: {host_part}")
    else:
        print("⚠️  No DATABASE_URL set, using SQLite")
    
    # Check required environment variables for production
    if IS_RENDER:
        required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY']
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            print(f"⚠️  Missing env vars: {', '.join(missing)}")
        else:
            print("✅ All required environment variables set")
    
    print("="*60)

def init_database_tables():
    """Initialize database tables"""
    print("\n" + "="*60)
    print("📦 DATABASE INITIALIZATION")
    print("="*60)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created/verified")
        
        # Get table count
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Total tables: {len(tables)}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to initialize tables: {e}")
        return False

def check_database_data():
    """Check if database has data"""
    print("\n" + "="*60)
    print("📊 DATABASE STATUS")
    print("="*60)
    
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        
        # Check if tables have data
        tables_to_check = ['users', 'books', 'chapters', 'verses', 'questions']
        
        for table in tables_to_check:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                if count > 0:
                    print(f"  ✅ {table}: {count:,} rows")
                else:
                    print(f"  ⚠️  {table}: empty")
            except Exception as e:
                print(f"  ❌ {table}: error - {e}")
        
        db.close()
        print("="*60)
        return True
    except Exception as e:
        print(f"❌ Failed to check data: {e}")
        return False

def run_migration():
    """Run database migration"""
    print("\n" + "="*60)
    print("🔄 RUNNING DATABASE MIGRATION")
    print("="*60)
    
    try:
        # This is a simple migration - just ensure all tables exist
        # For complex migrations, use Alembic
        Base.metadata.create_all(bind=engine)
        print("✅ Schema updated successfully")
        
        # Check for any missing columns (basic check)
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        # Define expected columns for each table (add as needed)
        expected_columns = {
            'users': ['id', 'username', 'email', 'password_hash', 'is_admin', 'google_id', 'auth_provider'],
            'books': ['id', 'name', 'testament_id'],
            'chapters': ['id', 'book_id', 'chapter_number'],
            'verses': ['id', 'chapter_id', 'verse_number'],
            'questions': ['id', 'book_id', 'chapter_id', 'level_id', 'correct_option']
        }
        
        for table_name, columns in expected_columns.items():
            if table_name in inspector.get_table_names():
                existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
                missing = [col for col in columns if col not in existing_columns]
                if missing:
                    print(f"⚠️  Table {table_name} missing columns: {missing}")
                    print(f"   You may need to add them manually or update models")
        
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def reset_database():
    """Reset database - delete all data"""
    print("\n" + "="*60)
    print("⚠️  DATABASE RESET - DESTRUCTIVE OPERATION")
    print("="*60)
    
    confirm = input("Are you sure you want to DELETE ALL DATA? Type 'YES' to confirm: ")
    if confirm != 'YES':
        print("❌ Reset cancelled")
        return False
    
    confirm2 = input("Type 'DELETE' to permanently delete all data: ")
    if confirm2 != 'DELETE':
        print("❌ Reset cancelled")
        return False
    
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
        
        # Recreate tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables recreated")
        
        print("\n✅ Database has been reset successfully")
        return True
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return False

def start_server(host='0.0.0.0', port=5000, debug=False):
    """Start the Flask server"""
    print_banner()
    check_environment()
    
    # Test database connection
    print("\n" + "="*60)
    print("🔌 DATABASE CONNECTION")
    print("="*60)
    
    if test_connection():
        print("✅ Database connection established")
    else:
        print("❌ Cannot start server - database connection failed")
        sys.exit(1)
    
    # Initialize tables if needed
    init_database_tables()
    
    # Show database status
    check_database_data()
    
    # Create app
    app = create_app()
    
    # Determine if running on Render
    IS_RENDER = os.environ.get('RENDER') or os.environ.get('DATABASE_URL')
    
    print("\n" + "="*60)
    print("🚀 STARTING SERVER")
    print("="*60)
    print(f"📍 URL: http://{host}:{port}")
    print(f"📚 Swagger UI: http://{host}:{port}/apidocs/")
    print(f"💚 Health Check: http://{host}:{port}/health")
    print(f"🌍 Environment: {'Render Production' if IS_RENDER else 'Local Development'}")
    print("="*60)
    print("⚡ Press CTRL+C to stop the server")
    print("="*60 + "\n")
    
    # Run the server
    if IS_RENDER:
        # Production server (for Render)
        from werkzeug.serving import run_simple
        run_simple(
            host,
            port,
            app,
            use_reloader=False,
            use_debugger=False,
            threaded=True
        )
    else:
        # Development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=True
        )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Bible Quiz API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    parser.add_argument('--migrate', action='store_true', help='Run database migration')
    parser.add_argument('--reset-db', action='store_true', help='Reset database (deletes all data)')
    parser.add_argument('--status', action='store_true', help='Show database status only')
    
    args = parser.parse_args()
    
    # Handle database operations
    if args.reset_db:
        reset_database()
        return
    
    if args.init_db:
        init_database_tables()
        return
    
    if args.migrate:
        run_migration()
        return
    
    if args.status:
        check_environment()
        check_database_data()
        return
    
    # Start server
    start_server(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()