import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def init_db():
    # Get the database URL from the environment variable
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set.")
        return

    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Connect to the database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Create the conversations table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                sender VARCHAR(100) PRIMARY KEY,
                messages TEXT,
                openai_thread_id VARCHAR(100)
            )
        ''')
        
        # Commit the changes
        conn.commit()
        print("Database initialized successfully.")
    except psycopg2.Error as e:
        print(f"An error occurred while initializing the database: {e}")
    finally:
        # Close the cursor and connection
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_db()