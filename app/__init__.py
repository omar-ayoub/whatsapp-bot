import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'hard to guess string'
    app.config['VERIFY_TOKEN'] = os.environ.get('VERIFY_TOKEN')
    app.config['WHATSAPP_TOKEN'] = os.environ.get('WHATSAPP_TOKEN')
    app.config['WHATSAPP_PHONE_NUMBER_ID'] = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    app.config['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')
    app.config['OPENAI_ASSISTANT_ID'] = os.environ.get('OPENAI_ASSISTANT_ID')
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Import models
    from .models import User, Thread, Message

    # Create all database tables
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database tables recreated successfully")
        try:
            db.engine.connect()
            print("Database connection successful")
        except Exception as e:
            print(f"Database connection failed: {str(e)}")

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
