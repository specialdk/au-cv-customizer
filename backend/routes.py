from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Document

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
