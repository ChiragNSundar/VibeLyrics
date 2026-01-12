import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), 'data', 'vibelyrics.db')

def migrate_db():
    print(f"Connecting to {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(user_profiles)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add favorite_words
        if 'favorite_words' not in columns:
            print("Adding favorite_words column...")
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN favorite_words TEXT DEFAULT '[]'")
            
        # Add banned_words
        if 'banned_words' not in columns:
            print("Adding banned_words column...")
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN banned_words TEXT DEFAULT '[]'")
            
        # Add slang_preferences
        if 'slang_preferences' not in columns:
            print("Adding slang_preferences column...")
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN slang_preferences TEXT DEFAULT '[]'")
            
        conn.commit()
        print("Migration successful!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
