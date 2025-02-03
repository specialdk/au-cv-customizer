from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import logging
from backend.database import db
from backend.models import User

logger = logging.getLogger(__name__)

def init_auth_routes(app):
    @app.route('/api/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            
            # Check if user already exists
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already registered'}), 400
                
            # Create new user
            user = User(
                email=data['email'],
                name=data['name']
            )
            user.set_password(data['password'])
            
            db.session.add(user)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'message': 'User registered successfully',
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name
                }
            }), 201
            
        except KeyError as e:
            logger.error(f'[register] Missing field: {str(e)}')
            return jsonify({'error': f'Missing field: {str(e)}'}), 400
            
        except Exception as e:
            logger.error(f'[register] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            
            # Find user by email
            user = User.query.filter_by(email=data['email']).first()
            
            if not user or not user.check_password(data['password']):
                return jsonify({'error': 'Invalid email or password'}), 401
                
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name
                }
            }), 200
            
        except KeyError as e:
            logger.error(f'[login] Missing field: {str(e)}')
            return jsonify({'error': f'Missing field: {str(e)}'}), 400
            
        except Exception as e:
            logger.error(f'[login] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/user', methods=['GET'])
    @jwt_required()
    def get_user():
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            return jsonify({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name
                }
            }), 200
            
        except Exception as e:
            logger.error(f'[get_user] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    return app
