import warnings
warnings.filterwarnings("ignore")
from app.db.session import SessionLocal
from sqlalchemy import text
from app.core.security import verify_password
import sys

def check():
    print("Checking...", flush=True)
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT password_hash FROM users WHERE email='admin@verisca.com'"))
        row = result.first()
        if row:
            hash_val = row[0]
            print(f"Hash found: {hash_val[:15]}...", flush=True)
            is_valid = verify_password("password123", hash_val)
            print(f"Is valid: {is_valid}", flush=True)
        else:
            print("User not found", flush=True)
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import os
    sys.path.append(os.getcwd())
    check()
