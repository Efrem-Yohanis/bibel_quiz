# wsgi.py
"""
WSGI entry point for Gunicorn on Render
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the create_app function
from app import create_app

# Create the application instance - THIS MUST BE NAMED 'app'
app = create_app()

# For debugging (optional)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)