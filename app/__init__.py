from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
import os
import logging

db = SQLAlchemy()

def create_app(config_name='production'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    logging.basicConfig(level=logging.DEBUG)
    app.logger.debug(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    db.init_app(app)
    
    with app.app_context():
        try:
            db.create_all()
            app.logger.debug("Database tables created successfully.")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
    
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app