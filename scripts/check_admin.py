import sys
from pathlib import Path
# Ensure project root is on sys.path so `import app` works when running this script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.init_db import DB_PATH
import sqlite3

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT id, username, email, is_admin FROM users WHERE username = ?", ('efrem',))
row = c.fetchone()
if row:
    print({'id': row['id'], 'username': row['username'], 'email': row['email'], 'is_admin': bool(row['is_admin'])})
else:
    print('Not found')
conn.close()
