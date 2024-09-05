import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'hard to guess string'
    app.config['VERIFY_TOKEN'] = os.environ.get('VERIFY_TOKEN')
    app.config['WHATSAPP_TOKEN'] = os.environ.get('WHATSAPP_TOKEN')
    app.config['WHATSAPP_PHONE_NUMBER_ID'] = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    app.config['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')
    app.config['OPENAI_ASSISTANT_ID'] = os.environ.get('OPENAI_ASSISTANT_ID')

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app