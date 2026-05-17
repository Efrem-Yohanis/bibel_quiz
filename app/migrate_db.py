import sqlite3
import psycopg2
from psycopg2.extras import execute_values

# Configurations
SQLITE_DB_PATH = "../bible_quiz.db" # Adjusted path since you are in the /app folder
POSTGRES_URL = "postgresql://bibel_quiz_user:IBQceDb477BJ0i7DWL4MSIOy6hnkATEO@dpg-d84b0f58nd3s73ctqle0-a.oregon-postgres.render.com/bibel_quiz"

print("🚀 Starting pure-Python migration (No SQLAlchemy)...")

# Connect to databases
sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
sqlite_cursor = sqlite_conn.cursor()

pg_conn = psycopg2.connect(POSTGRES_URL)
pg_cursor = pg_conn.cursor()

# Get all tables from SQLite
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in sqlite_cursor.fetchall() if not row[0].startswith('sqlite_')]

for table_name in tables:
    if table_name == "alembic_version":
        continue

    print(f"📦 Migrating table: {table_name}...")

    # 1. Fetch column data from SQLite
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [f'"{col[1]}"' for col in sqlite_cursor.fetchall()] # Wrap in quotes for Postgres case sensitivity
    col_names_str = ", ".join(columns)

    # 2. Fetch all rows from SQLite
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()

    if not rows:
        print(f"   ℹ️ Table {table_name} is empty. Skipping.")
        continue

    # 3. Clear existing data in Postgres to avoid duplication
    pg_cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")

    # 4. Fast batch insert into Postgres
    insert_query = f"INSERT INTO {table_name} ({col_names_str}) VALUES %s"
    execute_values(pg_cursor, insert_query, rows)
    
    print(f"   ✅ Successfully migrated {len(rows)} rows.")

# Commit changes and close
pg_conn.commit()
sqlite_conn.close()
pg_conn.close()

print("\n🎉 Migration completed successfully via pure Python!")