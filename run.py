from app import create_app, db
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    app = create_app()
    with app.app_context():
        db.create_all()
        logger.debug("Database tables created in run.py")
except Exception as e:
    logger.error(f"Error creating app or database: {str(e)}")
    raise

if __name__ == '__main__':
    app.run()