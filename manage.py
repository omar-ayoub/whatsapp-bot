from flask.cli import FlaskGroup
from app import create_app
from init_db import init_db

cli = FlaskGroup(create_app=create_app)

@cli.command("init_db")
def init_db_command():
    """Initialize the database."""
    init_db()
    print("Initialized the database.")

if __name__ == "__main__":
    cli()