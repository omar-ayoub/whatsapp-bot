from app import create_app
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from the .env file

# Print DATABASE_URL to ensure it is loaded correctly
print("DATABASE_URL:", os.getenv("DATABASE_URL"))
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)