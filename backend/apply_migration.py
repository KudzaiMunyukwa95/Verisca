import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Use External URL for local connection, Internal for Render
# Check .env first
DATABASE_URL = os.getenv("DATABASE_URL")

def apply_migration():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Read SQL file
        with open("../database/migrations/01_spatial_tables.sql", "r") as f:
            sql_commands = f.read()
            
        print("Executing migration...")
        cur.execute(sql_commands)
        conn.commit()
        
        print("Migration successful! Tables created.")
        
        # Verification
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cur.fetchall()
        print("Current tables:", [t[0] for t in tables])
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    apply_migration()
