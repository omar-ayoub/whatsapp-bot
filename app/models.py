from . import db
from datetime import datetime

# User model representing a user in the system
class User(db.Model):
    __tablename__ = 'users'  # Explicit table naming for clarity and consistency
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    threads = db.relationship('Thread', backref='user', lazy='select', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.phone_number}>'

# Thread model representing conversation threads associated with users
class Thread(db.Model):
    __tablename__ = 'threads'  # Explicit table naming
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    openai_thread_id = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    messages = db.relationship('Message', backref='thread', lazy='select', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Thread {self.openai_thread_id}>'

# Message model representing individual messages within a thread
class Message(db.Model):
    __tablename__ = 'messages'  # Explicit table naming
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_from_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender_phone = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Message {self.id} - {"User" if self.is_from_user else "Bot"}>'