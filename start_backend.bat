@echo off
cd /d C:\Users\speci\CascadeProjects\au-cv-customizer
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
set FLASK_APP=app.py
set FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
