# Australian CV Customizer

A web application designed for the Australian market that helps users customize their CVs and cover letters for specific job applications.

## Features

- User Authentication and Profile Management
- CV and Cover Letter Customization
- Document Formatting Preservation
- Preview and Editing Interface
- PDF Generation and Email Functionality
- Application Tracking Dashboard
- Subscription Management with Free Trial
- Administrator Dashboard

## Tech Stack

- Backend: Python Flask
- Frontend: React
- Database: PostgreSQL
- Payment Processing: Stripe
- Document Processing: python-docx, reportlab
- Authentication: JWT

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   FLASK_APP=app
   FLASK_ENV=development
   DATABASE_URL=postgresql://username:password@localhost:5432/cv_customizer
   SECRET_KEY=your-secret-key
   STRIPE_SECRET_KEY=your-stripe-secret-key
   STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-specific-password
   ```

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

## Running the Application

1. Start the backend server:
   ```bash
   flask run
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm start
   ```

The application will be available at http://localhost:3000
