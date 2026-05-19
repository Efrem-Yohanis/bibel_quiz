import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so `import app` works when running this script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.init_db import init_database

# Set env vars for this process
os.environ['ADMIN_USERNAME'] = 'efrem'
os.environ['ADMIN_PASSWORD'] = 'Efrem12.'
os.environ['ADMIN_EMAIL'] = 'efremyohanis111@gmail.com'

if __name__ == '__main__':
    init_database()
