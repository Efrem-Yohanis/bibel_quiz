# scripts/check_row_counts.py
"""
Check row counts in SQLite database before migration
Run: python scripts/check_row_counts.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# ============ CONFIGURATION ============
SQLITE_PATH = Path(__file__).parent.parent / 'app' / 'bible_quiz.db'

def get_table_sizes():
    """Get row counts and approximate size for each table"""
    if not SQLITE_PATH.exists():
        print(f"❌ SQLite database not found at {SQLITE_PATH}")
        return None
    
    conn = sqlite3.connect(str(SQLITE_PATH))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = cursor.fetchall()
    
    # Get database file size
    db_size = SQLITE_PATH.stat().st_size
    db_size_mb = db_size / (1024 * 1024)
    
    print("\n" + "="*80)
    print("📊 SQLITE DATABASE STATISTICS")
    print("="*80)
    print(f"📁 Database file: {SQLITE_PATH}")
    print(f"💾 File size: {db_size_mb:.2f} MB")
    print(f"🕒 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    table_stats = []
    total_rows = 0
    
    for table in tables:
        table_name = table[0]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        total_rows += row_count
        
        # Get column count
        cursor.execute(f"PRAGMA table_info({table_name})")
        column_count = len(cursor.fetchall())
        
        # Estimate size per table (approximate)
        if row_count > 0:
            # Rough estimate: average row size * row count
            cursor.execute(f"SELECT AVG(LENGTH(CAST(COALESCE(id,0) AS TEXT))) FROM {table_name}")
            avg_id_len = cursor.fetchone()[0] or 0
            
            # Get sample data to estimate row size
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample_row = cursor.fetchone()
            if sample_row:
                avg_row_size = sum(len(str(val)) for val in sample_row if val) / len(sample_row)
                est_size_mb = (avg_row_size * row_count) / (1024 * 1024)
            else:
                est_size_mb = 0
        else:
            est_size_mb = 0
        
        table_stats.append({
            'name': table_name,
            'rows': row_count,
            'columns': column_count,
            'est_size_mb': est_size_mb
        })
    
    # Sort by row count (largest first)
    table_stats.sort(key=lambda x: x['rows'], reverse=True)
    
    # Display table statistics
    print("\n📋 TABLE ROW COUNTS:")
    print("-"*80)
    print(f"{'Table Name':<25} {'Rows':>12} {'Columns':>8} {'Est. Size (MB)':>15} {'Status':>10}")
    print("-"*80)
    
    for stat in table_stats:
        # Determine status based on row count
        if stat['rows'] == 0:
            status = "EMPTY"
        elif stat['rows'] < 100:
            status = "SMALL"
        elif stat['rows'] < 1000:
            status = "MEDIUM"
        elif stat['rows'] < 10000:
            status = "LARGE"
        else:
            status = "VERY LARGE"
        
        # Format row count with commas
        rows_str = f"{stat['rows']:,}"
        size_str = f"{stat['est_size_mb']:.2f}" if stat['est_size_mb'] > 0 else "0.00"
        
        print(f"{stat['name']:<25} {rows_str:>12} {stat['columns']:>8} {size_str:>15} {status:>10}")
    
    print("-"*80)
    print(f"{'TOTAL':<25} {total_rows:>12,}")
    print("="*80)
    
    # Show migration time estimate
    print("\n⏱️  MIGRATION TIME ESTIMATE:")
    print("-"*80)
    
    # Estimate based on typical speeds
    # ~500 rows/second for small tables, ~200 rows/second for large tables with text
    estimated_seconds = 0
    for stat in table_stats:
        if stat['rows'] < 1000:
            speed = 500  # rows per second
        elif stat['rows'] < 10000:
            speed = 300
        else:
            speed = 150
        
        if stat['rows'] > 0:
            table_seconds = stat['rows'] / speed
            estimated_seconds += table_seconds
            
            if stat['rows'] > 1000:  # Only show for larger tables
                minutes = table_seconds / 60
                print(f"  {stat['name']:<25} : {stat['rows']:>8,} rows ≈ {minutes:.1f} minutes")
    
    estimated_minutes = estimated_seconds / 60
    estimated_hours = estimated_minutes / 60
    
    print("-"*80)
    if estimated_hours >= 1:
        print(f"  ⏰ Total estimated time: {estimated_hours:.1f} hours ({estimated_minutes:.1f} minutes)")
    else:
        print(f"  ⏰ Total estimated time: {estimated_minutes:.1f} minutes")
    
    print("="*80)
    
    # Show table dependency order
    print("\n📋 RECOMMENDED MIGRATION ORDER (by dependencies):")
    print("-"*80)
    
    dependency_order = ['languages', 'levels', 'testaments', 'users', 'books', 'chapters', 
                        'verses', 'verse_texts', 'questions', 'question_texts', 'options', 
                        'option_texts', 'explanations', 'user_sessions', 'quiz_attempts', 
                        'quiz_answers', 'user_book_progress']
    
    for i, table in enumerate(dependency_order, 1):
        # Find actual row count
        for stat in table_stats:
            if stat['name'] == table:
                rows_str = f"{stat['rows']:,}"
                print(f"  {i:2}. {table:<25} : {rows_str:>12} rows")
                break
        else:
            print(f"  {i:2}. {table:<25} : {'N/A':>12} (not found)")
    
    print("="*80)
    
    # Show warnings for very large tables
    print("\n⚠️  IMPORTANT NOTES:")
    print("-"*80)
    
    for stat in table_stats:
        if stat['rows'] > 50000:
            print(f"  • {stat['name']} has {stat['rows']:,} rows - this will take significant time")
            print(f"    Consider using batch inserts and monitoring progress")
    
    if total_rows > 100000:
        print(f"\n  💡 Tip: With {total_rows:,} total rows, migration may take 30+ minutes")
        print(f"     Make sure you have a stable internet connection")
        print(f"     The script includes resumable capability - you can Ctrl+C and resume later")
    
    print("="*80 + "\n")
    
    conn.close()
    return table_stats, total_rows

def get_table_sample(table_name, limit=5):
    """Get sample data from a table"""
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        if rows:
            print(f"\n📋 Sample from {table_name}:")
            for i, row in enumerate(rows, 1):
                print(f"  Row {i}: {dict(row)}")
    except Exception as e:
        print(f"Error sampling {table_name}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n" + "🔍 ANALYZING DATABASE...")
    
    result = get_table_sizes()
    
    if result:
        table_stats, total_rows = result
        
        # Ask if user wants to see sample data
        print("\n" + "="*80)
        response = input("Do you want to see sample data from tables? (yes/no): ")
        if response.lower() == 'yes':
            for stat in table_stats[:5]:  # Show first 5 tables
                if stat['rows'] > 0:
                    get_table_sample(stat['name'], 2)
        
        # Ask if ready to migrate
        print("\n" + "="*80)
        print(f"📊 Summary: {len(table_stats)} tables, {total_rows:,} total rows")
        print("="*80)
        
        response = input("\nReady to start migration? (yes/no): ")
        if response.lower() == 'yes':
            print("\nStarting migration...")
            # Import and run migration
            from migrate_sqlite_to_postgres_complete import DataMigrator
            migrator = DataMigrator()
            migrator.run()
        else:
            print("Migration cancelled. Run the script again when ready.")
    else:
        print("Failed to analyze database")