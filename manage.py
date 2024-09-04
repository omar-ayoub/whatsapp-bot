from app import create_app, db
from app.models import Conversation

app = create_app()

@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created.")

if __name__ == "__main__":
    app.run()