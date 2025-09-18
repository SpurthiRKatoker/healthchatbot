from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# SQLAlchemy instance
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profiles = db.relationship('Profile', backref='user', lazy=True)

class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20))
    age = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chats = db.relationship('Chat', backref='profile', lazy=True)

class Chat(db.Model):
    __tablename__ = "chats"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
