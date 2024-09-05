import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def init_db():
    # Get the database URL from the environment variable
    database_url = os.environ['DATABASE_URL']
    
    # Connect to the database
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    try:
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
        print(f"An error occurred: {e}")
    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()

if __name__ == "__main__":
    init_db()