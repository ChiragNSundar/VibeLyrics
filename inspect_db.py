import sqlite3
import os

def inspect_db():
    db_path = os.path.join("data", "vibelyrics.db")
    print(f"Inspecting: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- lyric_lines Columns ---")
    try:
        cursor.execute("PRAGMA table_info(lyric_lines)")
        columns = cursor.fetchall()
        existing_cols = [col[1] for col in columns]
        for col in columns:
            print(f"{col[1]} ({col[2]})")
            
        # Add missing columns
        needed_cols = {
            "stress_pattern": "VARCHAR(100)",
            "syllable_count": "INTEGER DEFAULT 0",
            "rhyme_end": "VARCHAR(50)",
            "has_internal_rhyme": "BOOLEAN DEFAULT 0",
            "complexity_score": "FLOAT"
        }
        
        for name, type_def in needed_cols.items():
            if name not in existing_cols:
                print(f"Adding missing column: {name}")
                cursor.execute(f"ALTER TABLE lyric_lines ADD COLUMN {name} {type_def}")
        
        conn.commit()
        print("Schema update complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    inspect_db()
