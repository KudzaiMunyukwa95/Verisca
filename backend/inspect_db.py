import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def inspect_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # List all tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cur.fetchall()
        print("Tables:", [t[0] for t in tables])
        
        # Check claims columns if it exists
        if ('claims',) in tables:
            print("\nColumns in 'claims' table:")
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'claims';
            """)
            columns = cur.fetchall()
            for col in columns:
                print(f"- {col[0]}: {col[1]}")
        else:
            print("\n'claims' table does not exist.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
