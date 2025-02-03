from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import os

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_status = db.Column(db.String(20), default='trial')
    subscription_end_date = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(120))
    
    # Relationships
    documents = db.relationship('Document', backref='user', lazy=True)
    applications = db.relationship('JobApplication', backref='user', lazy=True)
    job_resources = db.relationship('JobResource', backref='user', lazy=True, order_by='desc(JobResource.created_at)')
    job_urls = db.relationship('JobURL', backref='user', lazy=True, order_by='desc(JobURL.created_at)')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        from app import app
        payload = {
            'user_id': self.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20))  # 'cv' or 'cover_letter'
    original_filename = db.Column(db.String(255))
    storage_path = db.Column(db.String(255))
    processing_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_title = db.Column(db.String(255))
    company_name = db.Column(db.String(255))
    job_url = db.Column(db.Text)
    contact_email = db.Column(db.String(120))
    contact_name = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    cv_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    cover_letter_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    status = db.Column(db.String(20))  # 'draft', 'submitted', 'in_progress', etc.
    applied_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)

class JobResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'url' or 'document'
    content = db.Column(db.Text, nullable=False)  # URL or filename
    file_path = db.Column(db.Text, nullable=True)  # Path to uploaded document, if applicable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<JobResource {self.type}: {self.content}>'

class JobURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.Text, nullable=False)
    job_title = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<JobURL {self.job_title} at {self.company_name}>'

class SubscriptionEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_type = db.Column(db.String(50))  # 'trial_started', 'subscription_started', 'windsurf_subscription', 'subscription_ended'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float)  # For payment events
    subscription_type = db.Column(db.String(50))  # 'trial', 'standard', 'windsurf'
    stripe_subscription_id = db.Column(db.String(120))  # Store Stripe subscription ID for reference
    duration_days = db.Column(db.Integer)  # Duration of the subscription
