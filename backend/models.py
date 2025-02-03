from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from backend.database import db

def get_current_time():
    # Get current time and format with timezone offset
    now = datetime.datetime.now()
    offset = '+10:00'  # AEST/AEDT
    return now.replace(microsecond=0)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, nullable=False, default=get_current_time)
    documents = db.relationship('Document', backref='owner', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    document_type = db.Column(db.String(50), default='cv')  # Type of document (cv, cover_letter, etc)
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Document {self.filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'document_type': self.document_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(200))
    company = db.Column(db.String(200))
    url = db.Column(db.String(500))
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='new')
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cv_id = db.Column(db.Integer, db.ForeignKey('documents.id'))

    def __repr__(self):
        return f'<Application {self.job_title} at {self.company}>'
