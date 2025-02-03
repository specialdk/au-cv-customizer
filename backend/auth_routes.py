from flask import request, jsonify
import bcrypt
import logging
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User

logger = logging.getLogger(__name__)

def init_auth_routes(app):
    @app.route('/api/register', methods=['POST'])
    def register():
        try:
            # Log raw request data
            logger.info(f'[register] Raw request data: {request.get_data()}')
            logger.info(f'[register] Request headers: {dict(request.headers)}')
            
            data = request.get_json()
            logger.info(f'[register] Parsed JSON data: {data}')
            
            email = data.get('email')
            password = data.get('password')
            name = data.get('name')

            logger.info(f'[register] Extracted fields - email: {email}, name: {name}, password length: {len(password) if password else 0}')

            if not email or not password or not name:
                missing_fields = []
                if not email: missing_fields.append('email')
                if not password: missing_fields.append('password')
                if not name: missing_fields.append('name')
                error_msg = f'Missing required fields: {", ".join(missing_fields)}'
                logger.error(f'[register] {error_msg}')
                return jsonify({'error': error_msg}), 400

            if User.query.filter_by(email=email).first():
                logger.error(f'[register] Email already exists: {email}')
                return jsonify({'error': 'Email already registered'}), 400

            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create new user
            user = User(
                email=email,
                password_hash=password_hash,
                name=name
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f'[register] User created with ID: {user.id}')
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            response_data = {
                'token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name
                }
            }
            
            logger.info(f'[register] Registration successful for email: {email}')
            logger.info(f'[register] Response data: {response_data}')
            
            return jsonify(response_data), 201

        except Exception as e:
            logger.error(f'[register] Error: {str(e)}')
            logger.exception(e)
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            logger.info(f'[login] Request data: {data}')
            
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                logger.error('[login] Missing email or password')
                return jsonify({'error': 'Email and password are required'}), 400

            user = User.query.filter_by(email=email).first()
            if not user:
                logger.error(f'[login] User not found for email: {email}')
                return jsonify({'error': 'Invalid email or password'}), 401

            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
                logger.error(f'[login] Invalid password for email: {email}')
                return jsonify({'error': 'Invalid email or password'}), 401

            # Create access token
            access_token = create_access_token(identity=user.id)
            
            response_data = {
                'token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name
                }
            }
            
            logger.info(f'[login] Login successful for email: {email}')
            logger.info(f'[login] Response data: {response_data}')
            
            return jsonify(response_data), 200

        except Exception as e:
            logger.error(f'[login] Error: {str(e)}')
            logger.exception(e)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            return jsonify({
                'id': user.id,
                'email': user.email,
                'name': user.name
            })
            
        except Exception as e:
            logger.error(f'[get_profile] Error: {str(e)}')
            logger.exception(e)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/profile', methods=['PUT'])
    @jwt_required()
    def update_profile():
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            data = request.get_json()
            if 'name' in data:
                user.name = data['name']
            if 'email' in data:
                user.email = data['email']
                
            db.session.commit()
            
            return jsonify({
                'id': user.id,
                'email': user.email,
                'name': user.name
            })
            
        except Exception as e:
            logger.error(f'[update_profile] Error: {str(e)}')
            logger.exception(e)
            return jsonify({'error': str(e)}), 500

    return app
