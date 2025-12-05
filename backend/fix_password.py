import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.security import get_password_hash

def fix_admin_password():
    print("Connecting to database...")
    db = SessionLocal()
    try:
        # Check if the user exists
        username = "admin@verisca.com"
        print(f"Looking for user: {username}")
        
        # We use raw SQL to avoid dependency on exact model structure potentially changing
        # But for now, let's try to update using a direct UPDATE statement
        
        # Valid bcrypt hash for 'password123'
        # Generated with: passlib.hash.bcrypt.hash("password123", rounds=12)
        # Or we can just generate a new one using our security module
        new_password = "password123"
        new_hash = get_password_hash(new_password)
        print(f"Generated new hash for '{new_password}': {new_hash}")
        
        # Update the user's password
        query = text("""
            UPDATE users 
            SET password_hash = :new_hash 
            WHERE email = :email OR username = :email
        """)
        
        result = db.execute(query, {"new_hash": new_hash, "email": username})
        db.commit()
        
        if result.rowcount > 0:
            print(f"SUCCESS: Updated password for {username}!")
        else:
            print(f"WARNING: User {username} not found in database.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure current directory is in python path if run directly
    import sys
    import os
    sys.path.append(os.getcwd())
    
    fix_admin_password()
