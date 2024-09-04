from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
import os

db = SQLAlchemy()

def create_app(config_name='production'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    
    with app.app_context():
        if not os.path.exists(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:////', '')):
            db.create_all()
            print("Database created.")
        else:
            print("Database already exists.")
    
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app