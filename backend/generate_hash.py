"""
Generate a password hash using bcrypt 4.0.1 (matching deployed version)
"""
from passlib.context import CryptContext

# Use the exact same configuration as in app/core/security.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = "password123"
hashed = pwd_context.hash(password)

print("=" * 60)
print("Password Hash Generated")
print("=" * 60)
print(f"Password: {password}")
print(f"Hash:     {hashed}")
print("=" * 60)
print("\nRun this SQL in pgAdmin:")
print()
print(f"UPDATE users SET password_hash = '{hashed}' WHERE username = 'admin';")
print()
