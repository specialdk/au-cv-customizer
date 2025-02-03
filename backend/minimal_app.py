from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import hashlib
import os
import traceback
import logging
from werkzeug.exceptions import HTTPException
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True

# Initialize extensions
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

@app.errorhandler(Exception)
def handle_error(error):
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    logger.error("Error: %s", str(error))
    logger.error("Traceback: %s", traceback.format_exc())
    response = {
        'error': str(error),
        'traceback': traceback.format_exc()
    }
    return make_response(jsonify(response), code)

@app.before_request
def log_request_info():
    logger.info('Headers: %s', dict(request.headers))
    logger.info('Body: %s', request.get_data(as_text=True))
    logger.info('URL: %s', request.url)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        logger.info("Received registration request")
        data = request.get_json()
        logger.info(f"Received data: {data}")
        
        if not data or not data.get('email') or not data.get('password'):
            logger.warning("Missing email or password")
            return jsonify({'error': 'Email and password are required'}), 400
        
        hashed = hashlib.sha256(data['password'].encode()).hexdigest()
        user = User(email=data['email'], password=hashed)
        db.session.add(user)
        db.session.commit()
        
        logger.info("User registered successfully")
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        logger.error("Registration error: %s", str(e))
        logger.error("Traceback: %s", traceback.format_exc())
        db.session.rollback()
        raise

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # Start fresh
        db.create_all()
    app.run(debug=True, port=5000)
