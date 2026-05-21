# run.py
import os
import sys
from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Check if running on Render
    is_render = os.environ.get('RENDER') == 'true'
    
    if is_render:
        # Production server
        print("\n" + "="*60)
        print("🚀 STARTING ON RENDER - PRODUCTION MODE")
        print("="*60)
        print(f"📡 Server running on port: {port}")
        print("="*60 + "\n")
        
        # For production, use gunicorn (which will be called from render.yaml)
        # This block is only for direct execution
        from werkzeug.serving import run_simple
        run_simple(
            '0.0.0.0',
            port,
            app,
            use_reloader=False,
            use_debugger=False,
            threaded=True
        )
    else:
        # Local development
        print("\n" + "="*60)
        print("💻 LOCAL DEVELOPMENT SERVER")
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