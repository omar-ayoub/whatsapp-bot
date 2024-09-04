from . import db

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), unique=True, nullable=False)
    messages = db.Column(db.Text)
    openai_thread_id = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return f'<Conversation {self.sender}>'