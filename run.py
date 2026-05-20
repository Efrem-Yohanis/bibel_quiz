# run.py
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("="*60)
    print("🚀 Bible Quiz API - Local Development Server")
    print("="*60)
    print(f"📍 URL: http://localhost:{port}")
    print(f"📚 Swagger UI: http://localhost:{port}/apidocs/")
    print(f"💚 Health Check: http://localhost:{port}/health")
    print(f"🔐 Google OAuth: Configured")
    print("="*60)
    print("⚡ Press CTRL+C to stop the server")
    print("="*60)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=True
    )