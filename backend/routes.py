from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Document, JobResource
from document_processing.job_scraper import JobScraper

logger = logging.getLogger(__name__)

# Configure allowed extensions
ALLOWED_EXTENSIONS = {'docx', 'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_routes(app):
    @app.route('/api/documents/upload', methods=['POST'])
    @jwt_required()
    def upload_document():
        """Upload a document (CV)."""
        try:
            current_user = get_jwt_identity()
            logger.info(f'[upload_document] Current user ID: {current_user}')
            logger.info(f'[upload_document] Request files: {request.files}')
            logger.info(f'[upload_document] Request headers: {dict(request.headers)}')
            
            # Check if file was uploaded
            if 'file' not in request.files:
                logger.error('[upload_document] No file part in request')
                return jsonify({'error': 'No file part'}), 400
                
            file = request.files['file']
            
            # Check if a file was selected
            if file.filename == '':
                logger.error('[upload_document] No selected file')
                return jsonify({'error': 'No selected file'}), 400
                
            # Check file type
            if not allowed_file(file.filename):
                logger.error(f'[upload_document] Invalid file type: {file.filename}')
                return jsonify({'error': 'Invalid file type. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS)}), 400
                
            # Secure the filename
            filename = secure_filename(file.filename)
            
            # Create a unique filename to avoid collisions
            base_name, extension = os.path.splitext(filename)
            storage_filename = f"{base_name}_{current_user}{extension}"
            storage_path = os.path.join(current_app.config['UPLOAD_FOLDER'], storage_filename)
            
            # Save the file
            file.save(storage_path)
            logger.info(f'[upload_document] File saved to {storage_path}')
            
            # Create document record
            document = Document(
                filename=filename,
                original_filename=filename,
                storage_path=storage_path,
                user_id=current_user,
                type='cv'  # Set document type
            )
            
            db.session.add(document)
            db.session.commit()
            logger.info(f'[upload_document] Document record created with ID: {document.id}')
            
            return jsonify({
                'message': 'File uploaded successfully',
                'document': {
                    'id': document.id,
                    'filename': document.filename,
                    'type': 'cv',
                    'processing_status': 'completed'
                }
            }), 201
            
        except Exception as e:
            logger.error(f'[upload_document] Error: {str(e)}')
            logger.exception(e)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents/<int:document_id>/status', methods=['GET'])
    @jwt_required()
    def get_document_status(document_id):
        """Get the status of a document."""
        try:
            current_user = get_jwt_identity()
            document = Document.query.filter_by(id=document_id, user_id=current_user).first()
            
            if not document:
                logger.error(f'[get_document_status] Document not found: {document_id}')
                return jsonify({'error': 'Document not found'}), 404
                
            return jsonify({
                'id': document.id,
                'filename': document.filename,
                'processing_status': 'completed'  # For now, we'll assume it's always completed
            })
            
        except Exception as e:
            logger.error(f'[get_document_status] Error: {str(e)}')
            logger.exception(e)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/jobs/parse', methods=['POST'])
    @jwt_required()
    def parse_job():
        """Parse a job posting URL."""
        try:
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return jsonify({'error': 'URL is required'}), 400
                
            # Initialize scraper
            scraper = JobScraper()
            
            # Scrape job posting
            job_data = scraper.scrape_job_posting(url)
            
            # Store in database
            job = JobResource(
                url=url,
                title=job_data.get('title', ''),
                company=job_data.get('company', ''),
                location=job_data.get('location', ''),
                description=job_data.get('description', ''),
                requirements=job_data.get('sections', {}).get('requirements', ''),
                responsibilities=job_data.get('sections', {}).get('responsibilities', ''),
                user_id=get_jwt_identity()
            )
            
            db.session.add(job)
            db.session.commit()
            
            return jsonify({
                'message': 'Job posting parsed successfully',
                'job': {
                    'id': job.id,
                    'url': job.url,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'requirements': job.requirements,
                    'responsibilities': job.responsibilities
                }
            }), 201
            
        except Exception as e:
            logger.error(f'[parse_job] Error: {str(e)}')
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents/cv', methods=['GET'])
    @jwt_required()
    def get_user_cv():
        """Get the user's most recent CV."""
        try:
            current_user = get_jwt_identity()
            
            # Get user's most recent CV
            cv = Document.query.filter_by(
                user_id=current_user,
                type='cv'
            ).order_by(Document.created_at.desc()).first()
            
            if not cv:
                return jsonify({'error': 'No CV found'}), 404
                
            return jsonify({
                'id': cv.id,
                'filename': cv.original_filename,
                'uploadTime': cv.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f'[get_user_cv] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/jobs', methods=['GET'])
    @jwt_required()
    def get_user_jobs():
        """Get all jobs added by the user."""
        try:
            current_user = get_jwt_identity()
            
            # Get user's jobs
            jobs = JobResource.query.filter_by(
                user_id=current_user
            ).order_by(JobResource.created_at.desc()).all()
            
            return jsonify([{
                'id': job.id,
                'url': job.url,
                'title': job.title,
                'company': job.company,
                'created_at': job.created_at.isoformat()
            } for job in jobs])
            
        except Exception as e:
            logger.error(f'[get_user_jobs] Error: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/jobs/urls', methods=['POST'])
    @jwt_required()
    def add_job_url():
        """Add a new job URL."""
        try:
            current_user = get_jwt_identity()
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return jsonify({'error': 'URL is required'}), 400
                
            # Create new job resource
            job = JobResource(
                url=url,
                user_id=current_user,
                title='New Position',  # We'll update this later with scraping
                company='Company Name'  # We'll update this later with scraping
            )
            
            db.session.add(job)
            db.session.commit()
            
            return jsonify({
                'id': job.id,
                'url': job.url,
                'title': job.title,
                'company': job.company,
                'created_at': job.created_at.isoformat()
            }), 201
            
        except Exception as e:
            logger.error(f'[add_job_url] Error: {str(e)}')
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
