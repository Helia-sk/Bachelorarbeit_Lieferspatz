#!/usr/bin/env python3
import sqlite3
import os

def check_database():
    db_path = 'user_logs.db'
    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("❌ Database file does not exist!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in database: {tables}")
        
        # Check if user_interactions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_interactions'")
        user_interactions_table = cursor.fetchone()
        print(f"user_interactions table exists: {user_interactions_table}")
        
        if user_interactions_table:
            # Check table structure
            cursor.execute("PRAGMA table_info(user_interactions)")
            columns = cursor.fetchall()
            print(f"Table columns: {columns}")
            
            # Check row count
            cursor.execute("SELECT COUNT(*) FROM user_interactions")
            row_count = cursor.fetchone()[0]
            print(f"Row count: {row_count}")
        
        conn.close()
        print("✅ Database check completed")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()
