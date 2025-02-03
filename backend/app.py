import os
import sys
import logging
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db, User, Document, Application

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3002"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
jwt = JWTManager(app)

# Configure SQLAlchemy
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"Current directory: {os.getcwd()}")
print(f"Database file location: {db_path}")

# Initialize database
db.init_app(app)

# Create required directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Ensure all models are imported before creating tables
from models import User, Document, Application

# Create database tables within app context
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
        # Verify tables
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        raise

@app.before_request
def log_request_info():
    logger.info('Headers: %s', dict(request.headers))
    logger.info('Body: %s', request.get_data())

# Import routes after app is created to avoid circular imports
from auth_routes import init_auth_routes
from routes import init_routes

# Initialize routes
init_auth_routes(app)
init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
