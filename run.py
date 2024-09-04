from app import create_app
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    app = create_app()
except Exception as e:
    logger.error(f"Error creating app: {str(e)}")
    raise

if __name__ == '__main__':
    app.run()