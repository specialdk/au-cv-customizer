from flask import jsonify, request, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from backend.app import app, db
import stripe
from models import User, Document, JobApplication, SubscriptionEvent, JobURL, JobResource
from document_processing.job_scraper import JobScraper
from document_processing.cv_parser import CVParser
import os
from datetime import datetime, timedelta
import jwt
from functools import wraps
import re

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            app.logger.error('[token_required] Token is missing')
            return jsonify({'message': 'Token is missing'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                app.logger.error(f'[token_required] User not found for id {data.get("user_id")}')
                return jsonify({'message': 'User not found'}), 401
                
            app.logger.info(f'[token_required] Authenticated user {current_user.id}')
            return f(current_user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            app.logger.error('[token_required] Token has expired')
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            app.logger.error('[token_required] Token is invalid')
            return jsonify({'message': 'Token is invalid'}), 401
        except Exception as e:
            app.logger.error(f'[token_required] Error processing token: {str(e)}')
            return jsonify({'message': 'Error processing token'}), 401
    return decorated

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        app.logger.info(f'[register] Registration attempt with data: {data}')
        
        if not data:
            app.logger.error('[register] No data provided')
            return jsonify({'message': 'No data provided'}), 400

        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if not email or not password or not name:
            app.logger.error('[register] Missing required fields')
            return jsonify({'message': 'Email, password, and name are required'}), 400
            
        if User.query.filter_by(email=email).first():
            app.logger.error(f'[register] Email already registered: {email}')
            return jsonify({'message': 'Email already registered'}), 400
            
        # Create user
        user = User(
            email=email,
            name=name,
            password_hash=generate_password_hash(password),
            subscription_status='trial',
            subscription_end_date=datetime.utcnow() + timedelta(days=7)
        )
        
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        
        app.logger.info(f'[register] User created successfully: {user.id}')
        
        # Create and return token for immediate login
        token = jwt.encode(
            {
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(days=1)
            },
            app.config['JWT_SECRET_KEY'],
            algorithm="HS256"
        )
        
        return jsonify({
            'token': token,
            'message': 'Registration successful'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'[register] Error during registration: {str(e)}')
        app.logger.exception(e)
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        app.logger.info('[login] Login attempt')
        
        if not data:
            app.logger.error('[login] No data provided')
            return jsonify({'message': 'No data provided'}), 400
            
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            app.logger.error('[login] Email and password are required')
            return jsonify({'message': 'Email and password are required'}), 400
            
        user = User.query.filter_by(email=email).first()
        app.logger.info(f'[login] Found user: {user is not None}')
        
        if user and check_password_hash(user.password_hash, password):
            token = jwt.encode(
                {
                    'user_id': user.id,
                    'exp': datetime.utcnow() + timedelta(days=1)
                },
                app.config['JWT_SECRET_KEY'],
                algorithm="HS256"
            )
            app.logger.info(f'[login] Login successful for user {user.id}')
            return jsonify({'token': token})
        
        app.logger.error('[login] Invalid credentials')
        return jsonify({'message': 'Invalid credentials'}), 401
    except Exception as e:
        app.logger.error(f'[login] Error during login: {str(e)}')
        return jsonify({'message': 'Error during login'}), 500

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        app.logger.info(f'[get_profile] Getting profile for user {current_user.id}')
        return jsonify({
            'id': current_user.id,
            'email': current_user.email,
            'name': current_user.name
        })
    except Exception as e:
        app.logger.error(f'[get_profile] Error getting profile: {str(e)}')
        app.logger.exception(e)
        return jsonify({'message': 'Error getting profile'}), 500

@app.route('/api/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        data = request.get_json()
        app.logger.info(f'[update_profile] Updating profile for user {current_user.id}')
        
        if 'name' in data:
            current_user.name = data['name']
        if 'email' in data:
            current_user.email = data['email']
            
        db.session.commit()
        
        return jsonify({
            'id': current_user.id,
            'email': current_user.email,
            'name': current_user.name
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'[update_profile] Error updating profile: {str(e)}')
        app.logger.exception(e)
        return jsonify({'message': 'Error updating profile'}), 500

@app.route('/api/documents/upload', methods=['POST'])
@token_required
def upload_document(current_user):
    try:
        app.logger.info(f'[upload_document] Starting upload for user {current_user.id}')
        
        if 'file' not in request.files:
            app.logger.error('[upload_document] No file provided in request')
            return jsonify({'message': 'No file provided'}), 400
            
        file = request.files['file']
        doc_type = request.form.get('type', 'cv')  # Default to 'cv' if not specified
        
        if not file or not file.filename:
            app.logger.error('[upload_document] No file selected')
            return jsonify({'message': 'No file selected'}), 400
            
        # Quick save file without processing
        filename = secure_filename(file.filename)
        user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(user_upload_dir, exist_ok=True)
        
        storage_path = os.path.join(user_upload_dir, filename)
        app.logger.info(f'[upload_document] Saving file to {storage_path}')
        
        file.save(storage_path)
        
        # Create document record with processing_status
        document = Document(
            user_id=current_user.id,
            type=doc_type,
            original_filename=filename,
            storage_path=storage_path,
            processing_status='pending'  # Add this status field
        )
        
        db.session.add(document)
        db.session.commit()
        db.session.refresh(document)
        
        # Start async processing
        if doc_type == 'cv':
            # Use threading for async processing
            import threading
            def process_cv():
                try:
                    # Create a new database session for this thread
                    with app.app_context():
                        # Get a fresh copy of the document in this thread's session
                        doc = Document.query.get(document.id)
                        if not doc:
                            app.logger.error(f'[process_cv] Document {document.id} not found')
                            return
                            
                        try:
                            parser = CVParser()
                            parser.parse_docx(storage_path)
                            doc.processing_status = 'completed'
                            app.logger.info(f'[process_cv] Successfully processed document {doc.id}')
                        except Exception as e:
                            app.logger.error(f'[process_cv] Error processing CV: {str(e)}')
                            doc.processing_status = 'failed'
                        
                        db.session.commit()
                except Exception as e:
                    app.logger.error(f'[process_cv] Thread error: {str(e)}')
            
            thread = threading.Thread(target=process_cv)
            thread.daemon = True  # Make thread daemon so it doesn't block shutdown
            thread.start()
        
        app.logger.info(f'[upload_document] Document saved successfully with id {document.id}')
        
        return jsonify({
            'message': 'Document uploaded successfully',
            'document': {
                'id': document.id,
                'filename': filename,
                'type': doc_type,
                'processing_status': 'pending'
            }
        })
        
    except Exception as e:
        app.logger.error(f'[upload_document] Error during upload: {str(e)}')
        app.logger.exception(e)
        db.session.rollback()
        return jsonify({'message': f'Error uploading document: {str(e)}'}), 500

@app.route('/api/documents', methods=['GET'])
@token_required
def get_documents(current_user):
    documents = Document.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': doc.id,
        'type': doc.type,
        'original_filename': doc.original_filename,
        'storage_path': doc.storage_path,
        'created_at': doc.created_at.isoformat() if doc.created_at else None
    } for doc in documents])

@app.route('/api/documents/<int:document_id>', methods=['DELETE'])
@token_required
def delete_document(current_user, document_id):
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({'message': 'Document not found'}), 404
    
    try:
        # Delete the physical file
        if os.path.exists(document.storage_path):
            os.remove(document.storage_path)
        
        # Remove from database
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting document: {str(e)}'}), 500

@app.route('/api/documents/<int:document_id>/status', methods=['GET'])
@token_required
def get_document_status(current_user, document_id):
    try:
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            return jsonify({'message': 'Document not found'}), 404
            
        return jsonify({
            'id': document.id,
            'filename': document.original_filename,
            'type': document.type,
            'processing_status': document.processing_status
        })
        
    except Exception as e:
        app.logger.error(f'[get_document_status] Error: {str(e)}')
        return jsonify({'message': f'Error getting document status: {str(e)}'}), 500

@app.route('/api/applications', methods=['POST'])
@token_required
def create_application(current_user):
    try:
        data = request.get_json()
        app.logger.info(f'[create_application] Received data: {data}')
        
        if not data:
            app.logger.error('[create_application] No data provided')
            return jsonify({'message': 'No data provided'}), 400

        job_title = data.get('jobTitle')
        company_name = data.get('companyName')
        job_url = data.get('jobUrl')
        
        app.logger.info(f'[create_application] Parsed fields - Title: {job_title}, Company: {company_name}, URL: {job_url}')
        
        if not job_title:
            app.logger.error('[create_application] Job title is required')
            return jsonify({'message': 'Job title is required'}), 400
        if not company_name:
            app.logger.error('[create_application] Company name is required')
            return jsonify({'message': 'Company name is required'}), 400
        if not job_url:
            app.logger.error('[create_application] Job URL is required')
            return jsonify({'message': 'Job URL is required'}), 400
        
        application = JobApplication(
            user_id=current_user.id,
            job_title=job_title,
            company_name=company_name,
            job_url=job_url,
            status='draft'
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'application_id': application.id,
            'message': 'Application created successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'[create_application] Error creating application: {str(e)}')
        app.logger.exception(e)
        return jsonify({'message': f'Error creating application: {str(e)}'}), 500

@app.route('/api/applications', methods=['GET'])
@token_required
def get_applications(current_user):
    applications = JobApplication.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': app.id,
        'job_title': app.job_title,
        'company_name': app.company_name,
        'status': app.status,
        'applied_date': app.applied_date.isoformat() if app.applied_date else None
    } for app in applications])

@app.route('/api/subscribe', methods=['POST'])
@token_required
def create_subscription(current_user):
    try:
        data = request.get_json()
        
        # Create subscription with Stripe
        subscription = stripe.Subscription.create(
            customer=current_user.stripe_customer_id,
            items=[{'price': os.getenv('STRIPE_PRICE_ID')}],
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent']
        )
        
        return jsonify({
            'subscriptionId': subscription.id,
            'clientSecret': subscription.latest_invoice.payment_intent.client_secret
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/subscribe/windsurf', methods=['POST'])
@token_required
def create_windsurf_subscription(current_user):
    try:
        # Windsurf-specific subscription with unique pricing and features
        windsurf_price_id = os.getenv('WINDSURF_PRICE_ID')
        
        if not windsurf_price_id:
            return jsonify({'error': 'Windsurf subscription not configured'}), 400
        
        # Create Windsurf subscription with Stripe
        subscription = stripe.Subscription.create(
            customer=current_user.stripe_customer_id,
            items=[{'price': windsurf_price_id}],
            payment_behavior='default_incomplete',
            payment_settings={
                'save_default_payment_method': 'on_subscription',
                'payment_method_types': ['card']
            },
            metadata={
                'subscription_type': 'windsurf',
                'user_id': current_user.id
            },
            expand=['latest_invoice.payment_intent']
        )
        
        # Update user's subscription status
        current_user.subscription_status = 'windsurf'
        current_user.subscription_end_date = datetime.utcnow() + timedelta(days=365)  # 1-year Windsurf subscription
        db.session.commit()
        
        # Log subscription event
        subscription_event = SubscriptionEvent(
            user_id=current_user.id,
            event_type='windsurf_subscription_started',
            amount=subscription.plan.amount / 100  # Convert cents to dollars
        )
        db.session.add(subscription_event)
        db.session.commit()
        
        return jsonify({
            'subscriptionId': subscription.id,
            'clientSecret': subscription.latest_invoice.payment_intent.client_secret,
            'subscriptionType': 'windsurf'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/analyze-job', methods=['POST'])
@token_required
def analyze_job(current_user):
    """Analyze a job posting and suggest CV improvements."""
    try:
        data = request.get_json()
        app.logger.info(f'[analyze_job] Starting analysis for user {current_user.id}')
        app.logger.info(f'[analyze_job] Request data: {data}')
        
        job_url = data.get('job_url')
        cv_id = data.get('cv_id')
        
        if not job_url or not cv_id:
            app.logger.error('[analyze_job] Missing job_url or cv_id')
            return jsonify({'error': 'Missing job_url or cv_id'}), 400
            
        # Get CV content
        cv = Document.query.filter_by(id=cv_id, user_id=current_user.id).first()
        if not cv:
            app.logger.error(f'[analyze_job] CV not found: {cv_id}')
            return jsonify({'error': 'CV not found'}), 404
            
        # Get job posting content
        scraper = JobScraper()
        job_data = scraper.scrape_job_posting(job_url)
        app.logger.info(f'[analyze_job] Job data: {job_data}')
        
        if not job_data:
            app.logger.error('[analyze_job] Failed to extract job data')
            return jsonify({'error': 'Failed to extract job data'}), 400
            
        # Parse CV content
        cv_parser = CVParser()
        cv_content = cv_parser.parse_docx(cv.storage_path)
        app.logger.info(f'[analyze_job] CV content: {cv_content}')
        
        # Analyze matches and opportunities
        matches = []
        opportunities = []
        match_score = 0
        total_points = 0
        
        # Extract key requirements and skills
        key_points = []
        sections = job_data.get('sections', {})
        app.logger.info(f'[analyze_job] Job sections: {sections}')
        
        # Get requirements and responsibilities from sections
        if sections and isinstance(sections, dict):
            requirements = sections.get('requirements', '')
            responsibilities = sections.get('responsibilities', '')
            
            app.logger.info(f'[analyze_job] Requirements: {requirements}')
            app.logger.info(f'[analyze_job] Responsibilities: {responsibilities}')
            
            if isinstance(requirements, str):
                key_points.extend([p.strip() for p in requirements.split('\n') if p.strip()])
            if isinstance(responsibilities, str):
                key_points.extend([p.strip() for p in responsibilities.split('\n') if p.strip()])
            
        # If no structured sections found, use the full description
        if not key_points and isinstance(job_data.get('description'), str):
            description = job_data['description']
            app.logger.info(f'[analyze_job] Using full description: {description}')
            key_points.extend([p.strip() for p in description.split('\n') if p.strip()])
            
        app.logger.info(f'[analyze_job] Key points: {key_points}')
        
        if not key_points:
            app.logger.error('[analyze_job] No key points found in job data')
            return jsonify({'error': 'No analyzable content found in job posting'}), 400
            
        cv_text = ' '.join(str(v) for v in cv_content.values()).lower()
        
        # Analyze each key point
        for point in key_points:
            if point and len(point) > 10:  # Skip empty or very short points
                total_points += 1
                
                # Check if this requirement/responsibility is covered in the CV
                keywords = set(point.lower().split())
                if any(keyword in cv_text for keyword in keywords):
                    matches.append(point)
                    match_score += 1
                else:
                    opportunities.append(point)
                    
        # Calculate final match score
        if total_points > 0:
            match_score = (match_score / total_points) * 100
        else:
            match_score = 0
            
        app.logger.info(f'[analyze_job] Analysis complete for user {current_user.id}')
        app.logger.info(f'[analyze_job] Match score: {match_score}')
        app.logger.info(f'[analyze_job] Matches: {matches}')
        app.logger.info(f'[analyze_job] Opportunities: {opportunities}')
        
        return jsonify({
            'matchScore': round(match_score, 2),
            'matches': matches,
            'opportunities': opportunities
        })
        
    except Exception as e:
        app.logger.error(f'[analyze_job] Error during analysis: {str(e)}')
        app.logger.exception(e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/job-urls', methods=['POST'])
@token_required
def create_job_url(current_user):
    try:
        if not current_user:
            app.logger.error('[create_job_url] No authenticated user found')
            return jsonify({'message': 'Authentication required'}), 401

        data = request.get_json()
        app.logger.info(f'[create_job_url] Received data: {data}')
        
        if not data:
            app.logger.error('[create_job_url] No data provided')
            return jsonify({'message': 'No data provided'}), 400

        url = data.get('url')
        job_title = data.get('job_title')
        company_name = data.get('company_name')
        
        app.logger.info(f'[create_job_url] User {current_user.id} creating job URL - URL: {url}, Title: {job_title}, Company: {company_name}')
        
        if not url:
            app.logger.error('[create_job_url] URL is required')
            return jsonify({'message': 'URL is required'}), 400
        if not job_title:
            app.logger.error('[create_job_url] Job title is required')
            return jsonify({'message': 'Job title is required'}), 400
        if not company_name:
            app.logger.error('[create_job_url] Company name is required')
            return jsonify({'message': 'Company name is required'}), 400
        
        # URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Check if URL already exists for this user
        existing_url = JobURL.query.filter_by(user_id=current_user.id, url=url).first()
        if existing_url:
            app.logger.warning(f'[create_job_url] URL already exists: {url}')
            return jsonify({'message': 'This URL has already been added'}), 400
        
        app.logger.info(f'[create_job_url] Creating job URL with data - URL: {url}, Title: {job_title}, Company: {company_name}')
        job_url = JobURL(
            user_id=current_user.id,
            url=url,
            job_title=job_title,
            company_name=company_name
        )
        
        db.session.add(job_url)
        db.session.commit()
        db.session.refresh(job_url)  # Refresh to ensure we have the latest data

        # Verify the job URL was created correctly
        created_url = JobURL.query.get(job_url.id)
        if not created_url:
            app.logger.error(f'[create_job_url] Failed to retrieve created job URL with id {job_url.id}')
            return jsonify({'message': 'Failed to create job URL'}), 500
            
        app.logger.info(f'[create_job_url] Created job URL object: id={created_url.id}, title={created_url.job_title}, company={created_url.company_name}')
        
        response_data = {
            'id': created_url.id,
            'url': created_url.url,
            'job_title': created_url.job_title,
            'company_name': created_url.company_name,
            'created_at': created_url.created_at.isoformat()
        }
        app.logger.info(f'[create_job_url] Sending response: {response_data}')
        return jsonify(response_data)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'[create_job_url] Error creating job URL: {str(e)}')
        app.logger.exception(e)
        return jsonify({'message': f'Error creating job URL: {str(e)}'}), 500

@app.route('/api/job-urls', methods=['GET'])
@token_required
def get_job_urls(current_user):
    try:
        app.logger.info(f'Getting job URLs for user {current_user.id}')
        job_urls = JobURL.query.filter_by(user_id=current_user.id).order_by(JobURL.created_at.desc()).all()
        app.logger.info(f'Found {len(job_urls)} job URLs')
        
        result = [{
            'id': url.id,
            'url': url.url,
            'job_title': url.job_title,
            'company_name': url.company_name,
            'created_at': url.created_at.isoformat()
        } for url in job_urls]
        
        app.logger.info(f'Sending response: {result}')
        return jsonify(result)
    except Exception as e:
        app.logger.error(f'Error getting job URLs: {str(e)}')
        return jsonify({'message': f'Error getting job URLs: {str(e)}'}), 500

@app.route('/api/job-urls/<int:url_id>', methods=['DELETE'])
@token_required
def delete_job_url(current_user, url_id):
    job_url = JobURL.query.filter_by(id=url_id, user_id=current_user.id).first()
    
    if not job_url:
        return jsonify({'message': 'Job URL not found'}), 404
    
    db.session.delete(job_url)
    db.session.commit()
    
    return jsonify({'message': 'Job URL deleted successfully'}), 200

@app.route('/api/job-resources/url', methods=['POST'])
@token_required
def create_job_resource_url(current_user):
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'message': 'URL is required'}), 400
    
    # Optional: Add URL validation
    if not url.startswith(('http://', 'https://')):
        return jsonify({'message': 'Invalid URL format'}), 400
    
    job_resource = JobResource(
        user_id=current_user.id,
        type='url',
        content=url
    )
    
    db.session.add(job_resource)
    db.session.commit()
    
    return jsonify({
        'id': job_resource.id,
        'type': job_resource.type,
        'content': job_resource.content,
        'created_at': job_resource.created_at.isoformat()
    }), 201

@app.route('/api/job-resources/document', methods=['POST'])
@token_required
def create_job_document(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    # Secure filename and create unique filepath
    filename = secure_filename(file.filename)
    filepath = os.path.join(JOB_RESOURCES_FOLDER, f"{current_user.id}_{filename}")
    
    # Save the file
    file.save(filepath)
    
    # Create database record
    job_resource = JobResource(
        user_id=current_user.id,
        type='document',
        content=filename,
        file_path=filepath
    )
    
    db.session.add(job_resource)
    db.session.commit()
    
    return jsonify({
        'id': job_resource.id,
        'type': job_resource.type,
        'content': job_resource.content,
        'created_at': job_resource.created_at.isoformat()
    }), 201

@app.route('/api/job-resources', methods=['GET'])
@token_required
def get_job_resources(current_user):
    job_resources = JobResource.query.filter_by(user_id=current_user.id).order_by(JobResource.created_at.desc()).all()
    return jsonify([{
        'id': resource.id,
        'type': resource.type,
        'content': resource.content,
        'created_at': resource.created_at.isoformat()
    } for resource in job_resources])

@app.route('/api/job-resources/<int:resource_id>', methods=['DELETE'])
@token_required
def delete_job_resource(current_user, resource_id):
    job_resource = JobResource.query.filter_by(id=resource_id, user_id=current_user.id).first()
    
    if not job_resource:
        return jsonify({'message': 'Job resource not found'}), 404
    
    # If it's a document, remove the physical file
    if job_resource.type == 'document' and job_resource.file_path:
        try:
            os.remove(job_resource.file_path)
        except FileNotFoundError:
            pass  # File already deleted or moved
    
    db.session.delete(job_resource)
    db.session.commit()
    
    return jsonify({'message': 'Job resource deleted successfully'}), 200

@app.route('/api/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': str(e)}), 400
        
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        user = User.query.filter_by(stripe_customer_id=subscription.customer).first()
        if user:
            user.subscription_status = 'active'
            user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)
            db.session.commit()
            
    return jsonify({'status': 'success'})

@app.route('/api/cv/pro-analysis', methods=['POST'])
@token_required
def pro_cv_analysis(current_user):
    """
    Pro-tier CV analysis endpoint
    Requires Windsurf Pro subscription
    """
    # Check if user has Pro subscription
    if current_user.subscription_status != 'windsurf':
        return jsonify({
            'error': 'Windsurf Pro subscription required',
            'status': 403
        }), 403
    
    # Check if file is uploaded
    if 'cv_file' not in request.files:
        return jsonify({
            'error': 'No CV file uploaded',
            'status': 400
        }), 400
    
    cv_file = request.files['cv_file']
    job_description = request.form.get('job_description', None)
    
    # Validate file
    if not cv_file or not cv_file.filename.endswith('.docx'):
        return jsonify({
            'error': 'Invalid file format. Please upload a .docx file',
            'status': 400
        }), 400
    
    try:
        # Save temporary file
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], cv_file.filename)
        cv_file.save(temp_path)
        
        # Perform Pro Analysis
        from cv_parser import analyze_cv_pro
        openai_key = os.getenv('OPENAI_API_KEY')
        
        analysis_result = analyze_cv_pro(
            temp_path, 
            job_description, 
            openai_key
        )
        
        # Clean up temporary file
        os.remove(temp_path)
        
        return jsonify({
            'cv_analysis': analysis_result,
            'status': 200
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'CV analysis failed: {str(e)}',
            'status': 500
        }), 500

@app.route('/api/generate-optimized-cv', methods=['POST'])
@token_required
def generate_optimized_cv(current_user):
    """Generate an optimized CV based on job requirements."""
    try:
        data = request.get_json()
        job_url = data.get('job_url')
        cv_id = data.get('cv_id')
        
        if not job_url or not cv_id:
            return jsonify({'error': 'Missing job_url or cv_id'}), 400
            
        # Get original CV
        cv = Document.query.filter_by(id=cv_id, user_id=current_user.id).first()
        if not cv:
            return jsonify({'error': 'CV not found'}), 404
            
        # Get job posting content
        scraper = JobScraper()
        job_data = scraper.scrape_job_posting(job_url)
        
        if not job_data:
            return jsonify({'error': 'Failed to extract job data'}), 400
            
        # Create a sanitized filename
        job_title = re.sub(r'[^\w\s-]', '', job_data['title'])
        company_name = re.sub(r'[^\w\s-]', '', job_data['company'])
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_name = f"CV_{job_title}_{company_name}_{timestamp}.docx"
        file_name = re.sub(r'\s+', '_', file_name)  # Replace spaces with underscores
            
        # Parse original CV
        cv_parser = CVParser()
        cv_content = cv_parser.parse_docx(cv.storage_path)
        
        # Create new CV document
        doc = Document()
        
        # Add header with contact information
        if 'contact' in cv_content:
            doc.add_paragraph(cv_content['contact'])
        
        # Add optimized professional summary
        doc.add_heading('Professional Summary', level=1)
        summary = generate_optimized_summary(cv_content.get('summary', ''), job_data)
        doc.add_paragraph(summary)
        
        # Add skills section, prioritizing matching skills
        doc.add_heading('Skills & Expertise', level=1)
        skills = prioritize_skills(cv_content.get('skills', ''), job_data)
        for skill in skills:
            doc.add_paragraph(skill, style='List Bullet')
        
        # Add experience section with enhanced descriptions
        doc.add_heading('Professional Experience', level=1)
        experience = enhance_experience(cv_content.get('experience', ''), job_data)
        doc.add_paragraph(experience)
        
        # Add education and other sections
        for section_name in ['education', 'certifications', 'projects']:
            if section_name in cv_content:
                doc.add_heading(section_name.title(), level=1)
                doc.add_paragraph(cv_content[section_name])
        
        # Save the new CV
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        doc.save(output_path)
        
        # Create new Document record
        new_cv = Document(
            user_id=current_user.id,
            storage_path=output_path,
            original_filename=file_name,
            type='optimized_cv',
            original_cv_id=cv_id  # Add reference to original CV
        )
        db.session.add(new_cv)
        db.session.commit()
        
        return jsonify({
            'message': 'CV optimized successfully',
            'cv_id': new_cv.id,
            'file_name': file_name,
            'download_url': f'/api/documents/{new_cv.id}/download'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_optimized_summary(original_summary: str, job_data: dict) -> str:
    """Generate an optimized professional summary focusing on job requirements."""
    # Extract key requirements
    requirements = []
    if 'requirements' in job_data['sections']:
        requirements.extend(job_data['sections']['requirements'].split('\n'))
    if 'responsibilities' in job_data['sections']:
        requirements.extend(job_data['sections']['responsibilities'].split('\n'))
    
    # Create a compelling summary that emphasizes matching qualifications
    key_points = [req.strip() for req in requirements if len(req.strip()) > 10][:3]
    
    summary = f"Experienced professional with proven expertise in {job_data['title']} roles. "
    summary += f"Demonstrated success in {', '.join(key_points)}. "
    summary += f"Seeking to leverage my skills and experience to drive success at {job_data['company']}."
    
    return summary

def prioritize_skills(original_skills: str, job_data: dict) -> list[str]:
    """Prioritize and enhance skills based on job requirements."""
    skills = original_skills.split('\n')
    job_text = ' '.join(job_data['sections'].values()).lower()
    
    # Sort skills by relevance to job posting
    return sorted(skills, key=lambda x: 1 if x.lower() in job_text else 0, reverse=True)

def enhance_experience(original_experience: str, job_data: dict) -> str:
    """Enhance experience descriptions to highlight relevant achievements."""
    # Extract key terms from job posting
    job_terms = set()
    for section in job_data['sections'].values():
        words = section.lower().split()
        job_terms.update(words)
    
    # Enhance each experience entry
    enhanced_entries = []
    entries = original_experience.split('\n\n')
    for entry in entries:
        # Highlight achievements that match job requirements
        enhanced_entry = entry
        for term in job_terms:
            if term in entry.lower():
                enhanced_entry = enhanced_entry.replace(
                    term,
                    term.upper()  # You might want to use a different emphasis method
                )
        enhanced_entries.append(enhanced_entry)
    
    return '\n\n'.join(enhanced_entries)

@app.route('/api/test-cv/<int:cv_id>', methods=['GET'])
@token_required
def test_cv_parse(current_user, cv_id):
    """Test endpoint to verify CV parsing."""
    try:
        # Get CV content
        cv = Document.query.filter_by(id=cv_id, user_id=current_user.id).first()
        if not cv:
            app.logger.error(f'[test_cv_parse] CV not found: {cv_id}')
            return jsonify({'error': 'CV not found'}), 404
            
        app.logger.info(f'[test_cv_parse] Found CV: {cv.filename} at {cv.storage_path}')
            
        # Parse CV content
        cv_parser = CVParser()
        cv_content = cv_parser.parse_docx(cv.storage_path)
        
        return jsonify({
            'success': True,
            'cv_content': cv_content
        })
        
    except Exception as e:
        app.logger.error(f'[test_cv_parse] Error: {str(e)}')
        app.logger.exception(e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-job', methods=['POST'])
@token_required
def test_job_parse(current_user):
    """Test endpoint to verify job parsing."""
    try:
        data = request.get_json()
        job_url = data.get('job_url')
        
        if not job_url:
            return jsonify({'error': 'Missing job_url'}), 400
            
        # Get job posting content
        scraper = JobScraper()
        job_data = scraper.scrape_job_posting(job_url)
        
        return jsonify({
            'success': True,
            'job_data': job_data
        })
        
    except Exception as e:
        app.logger.error(f'[test_job_parse] Error: {str(e)}')
        app.logger.exception(e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/users', methods=['GET'])
def debug_users():
    try:
        users = User.query.all()
        return jsonify([{
            'id': user.id,
            'email': user.email,
            'name': user.name
        } for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

JOB_RESOURCES_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'job_resources')
os.makedirs(JOB_RESOURCES_FOLDER, exist_ok=True)
