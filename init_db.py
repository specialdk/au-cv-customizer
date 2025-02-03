from app import db, app
from models import User, Document, JobApplication, SubscriptionEvent, JobURL, JobResource

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all existing tables.")
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
