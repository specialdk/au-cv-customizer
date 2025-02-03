import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from backend.app import app
from backend.models import User, Document, Application

def check_db():
    with app.app_context():
        users = User.query.all()
        documents = Document.query.all()
        applications = Application.query.all()
        
        print("\nDatabase Status:")
        print("-" * 50)
        print(f"Users: {len(users)}")
        for user in users:
            print(f"  - {user.email} ({user.name})")
        
        print(f"\nDocuments: {len(documents)}")
        for doc in documents:
            print(f"  - {doc.filename} (Owner: {doc.user_id})")
        
        print(f"\nApplications: {len(applications)}")
        for app in applications:
            print(f"  - {app.url} (User: {app.user_id})")

if __name__ == '__main__':
    check_db()
