import os
from flask import request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import logging
from backend.database import db
from backend.models import User, Document, Application

logger = logging.getLogger(__name__)

# Configure allowed extensions
ALLOWED_EXTENSIONS = {'docx', 'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_routes(app):
    @app.route('/api/documents/upload', methods=['POST'])
    @jwt_required()
    def upload_document():
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
                
            if not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file type. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS)}), 400
                
            if file:
                filename = secure_filename(file.filename)
                user_id = get_jwt_identity()
                
                # Create user directory if it doesn't exist
                user_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
                os.makedirs(user_dir, exist_ok=True)
                
                # Save file
                file_path = os.path.join(user_dir, filename)
                file.save(file_path)
                
                # Get document type from request
                document_type = request.form.get('document_type', 'cv')  # Default to 'cv' if not specified
                
                # Create document record
                document = Document(
                    filename=filename,
                    path=file_path,
                    document_type=document_type,
                    user_id=user_id
                )
                
                db.session.add(document)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'File uploaded successfully',
                    'document': document.to_dict()
                }), 201
                
        except Exception as e:
            logger.error(f'[upload_document] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents/<int:document_id>', methods=['GET'])
    @jwt_required()
    def get_document(document_id):
        try:
            user_id = get_jwt_identity()
            document = Document.query.filter_by(id=document_id, user_id=user_id).first()
            
            if not document:
                return jsonify({'error': 'Document not found'}), 404
                
            return send_from_directory(
                os.path.dirname(document.path),
                os.path.basename(document.path),
                as_attachment=True
            )
            
        except Exception as e:
            logger.error(f'[get_document] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents/<int:document_id>', methods=['DELETE'])
    @jwt_required()
    def delete_document(document_id):
        try:
            user_id = get_jwt_identity()
            
            # Find the document
            document = Document.query.filter_by(
                id=document_id,
                user_id=user_id
            ).first()
            
            if not document:
                return jsonify({'error': 'Document not found'}), 404
                
            # Delete the file if it exists
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                
            # Delete from database
            db.session.delete(document)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Document deleted successfully'
            }), 200
            
        except Exception as e:
            logger.error(f'[delete_document] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents', methods=['GET'])
    @jwt_required()
    def get_documents():
        try:
            user_id = get_jwt_identity()
            documents = Document.query.filter_by(user_id=user_id).all()
            
            return jsonify({
                'documents': [doc.to_dict() for doc in documents]
            }), 200
            
        except Exception as e:
            logger.error(f'[get_documents] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents/cv', methods=['GET'])
    @jwt_required()
    def get_user_cv():
        try:
            user_id = get_jwt_identity()
            cv = Document.query.filter_by(user_id=user_id, document_type='cv').order_by(Document.created_at.desc()).first()
            
            if not cv:
                return jsonify({'message': 'No CV found'}), 404
                
            return jsonify({
                'cv': cv.to_dict()
            }), 200
            
        except Exception as e:
            logger.error(f'[get_user_cv] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents/cv', methods=['DELETE'])
    @jwt_required()
    def delete_cv():
        try:
            user_id = get_jwt_identity()
            
            # Find the user's CV
            cv = Document.query.filter_by(
                user_id=user_id,
                document_type='cv'
            ).first()
            
            if not cv:
                return jsonify({'error': 'CV not found'}), 404
                
            # Delete the file if it exists
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], cv.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                
            # Delete from database
            db.session.delete(cv)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'CV deleted successfully'
            }), 200
            
        except Exception as e:
            logger.error(f'[delete_cv] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents/<int:document_id>/status', methods=['GET'])
    @jwt_required()
    def get_document_status(document_id):
        try:
            user_id = get_jwt_identity()
            document = Document.query.filter_by(id=document_id, user_id=user_id).first()
            
            if not document:
                return jsonify({'error': 'Document not found'}), 404
                
            return jsonify({
                'status': 'completed',  # For now, all uploads are considered completed immediately
                'document': document.to_dict()
            }), 200
            
        except Exception as e:
            logger.error(f'[get_document_status] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/applications', methods=['POST'])
    @jwt_required()
    def create_application():
        try:
            data = request.get_json()
            user_id = get_jwt_identity()
            
            application = Application(
                job_title=data['job_title'],
                company=data['company'],
                url=data.get('url'),
                description=data.get('description'),
                user_id=user_id,
                cv_id=data.get('cv_id')
            )
            
            db.session.add(application)
            db.session.commit()
            
            return jsonify({
                'message': 'Application created successfully',
                'application': {
                    'id': application.id,
                    'job_title': application.job_title,
                    'company': application.company,
                    'status': application.status,
                    'created_at': application.created_at.isoformat()
                }
            }), 201
            
        except KeyError as e:
            logger.error(f'[create_application] Missing field: {str(e)}')
            return jsonify({'error': f'Missing field: {str(e)}'}), 400
            
        except Exception as e:
            logger.error(f'[create_application] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/applications', methods=['GET'])
    @jwt_required()
    def get_applications():
        try:
            user_id = get_jwt_identity()
            applications = Application.query.filter_by(user_id=user_id).all()
            
            return jsonify({
                'applications': [{
                    'id': app.id,
                    'job_title': app.job_title,
                    'company': app.company,
                    'status': app.status,
                    'created_at': app.created_at.isoformat()
                } for app in applications]
            }), 200
            
        except Exception as e:
            logger.error(f'[get_applications] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/jobs', methods=['GET'])
    @jwt_required()
    def get_user_jobs():
        try:
            user_id = get_jwt_identity()
            
            # Get all jobs for the user
            jobs = Application.query.filter_by(user_id=user_id).all()
            
            return jsonify([{
                'id': job.id,
                'job_title': job.job_title,
                'company': job.company,
                'url': job.url,
                'description': job.description,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'updated_at': job.updated_at.isoformat()
            } for job in jobs]), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/jobs/urls', methods=['POST'])
    @jwt_required()
    def add_job_url():
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data or 'url' not in data:
                return jsonify({'error': 'URL is required'}), 400
            
            if 'job_title' not in data:
                return jsonify({'error': 'Job title is required'}), 400
                
            if 'company_name' not in data:
                return jsonify({'error': 'Company name is required'}), 400
                
            # Create a new job application with the URL
            application = Application(
                user_id=user_id,
                url=data['url'],
                job_title=data['job_title'],
                company=data['company_name']
            )
            
            db.session.add(application)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'id': application.id,
                    'url': application.url,
                    'job_title': application.job_title,
                    'company': application.company,
                    'created_at': application.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }), 201
            
        except Exception as e:
            logger.error(f'[add_job_url] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/jobs/urls/<int:job_id>', methods=['DELETE'])
    @jwt_required()
    def delete_job_url(job_id):
        try:
            user_id = get_jwt_identity()
            
            # Find the job
            job = Application.query.filter_by(
                id=job_id,
                user_id=user_id
            ).first()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
                
            # Delete from database
            db.session.delete(job)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Job deleted successfully'
            }), 200
            
        except Exception as e:
            logger.error(f'[delete_job_url] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    return app
