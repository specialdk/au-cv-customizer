from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.LargeBinary, nullable=False)  # Store hashed password as binary
    name = db.Column(db.String(120), nullable=True)  # User's name
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    documents = db.relationship('Document', backref='owner', lazy=True)
    applications = db.relationship('Application', backref='owner', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False, default='cv')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    job_url = db.Column(db.String(500))
    status = db.Column(db.String(50), default='active')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cv_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
