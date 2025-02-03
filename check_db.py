from app import app, db
from models import User

with app.app_context():
    users = User.query.all()
    print("\nRegistered Users:")
    print("----------------")
    if users:
        for user in users:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Name: {user.name}")
            print("----------------")
    else:
        print("No users found in database")
