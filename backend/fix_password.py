import warnings
warnings.filterwarnings("ignore")
import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.security import get_password_hash
import sys

def fix_admin_password():
    print("Connecting to database...", flush=True)
    try:
        db = SessionLocal()
        # Check if the user exists
        username = "admin@verisca.com"
        print(f"Looking for user: {username}", flush=True)
        
        # Valid bcrypt hash for 'password123'
        new_password = "password123"
        new_hash = get_password_hash(new_password)
        print(f"Generated new hash.", flush=True)
        
        # Update the user's password
        query = text("""
            UPDATE users 
            SET password_hash = :new_hash 
            WHERE email = :email OR username = :email
        """)
        
        result = db.execute(query, {"new_hash": new_hash, "email": username})
        db.commit()
        
        if result.rowcount > 0:
            print(f"SUCCESS: Updated password for {username}!", flush=True)
        else:
            print(f"WARNING: User {username} not found in database.", flush=True)
            
        db.close()
    except Exception as e:
        print(f"ERROR: {e}", flush=True)

if __name__ == "__main__":
    import os
    sys.path.append(os.getcwd())
    fix_admin_password()
