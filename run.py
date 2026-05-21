# run.py
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("\n" + "="*60)
    print("📖 BIBLE QUIZ API SERVER")
    print("="*60)
    print(f"📍 URL: http://localhost:{port}")
    print(f"📚 Swagger: http://localhost:{port}/apidocs/")
    print(f"💚 Health: http://localhost:{port}/health")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=True
    )