import bcrypt
import psycopg2
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def fix():
    print("Starting fix...", flush=True)
    if not DB_URL:
        print("Error: DATABASE_URL not found in environment", flush=True)
        return

    print("Generating hash...", flush=True)
    password = b"password123"
    # Generate salt and hash
    hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
    hash_str = hashed.decode('utf-8')
    print(f"New hash generated: {hash_str[:15]}...", flush=True)
    
    print("Connecting to DB...", flush=True)
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("Executing UPDATE...", flush=True)
        cur.execute("UPDATE users SET password_hash = %s WHERE email = 'admin@verisca.com'", (hash_str,))
        rows = cur.rowcount
        conn.commit()
        print(f"Updated {rows} rows.", flush=True)
        
        # Verify immediately
        cur.execute("SELECT password_hash FROM users WHERE email = 'admin@verisca.com'")
        row = cur.fetchone()
        if row:
            print(f"Verification: Hash in DB is now {row[0][:15]}...", flush=True)
        
        cur.close()
        conn.close()
        print("Done.", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    fix()
