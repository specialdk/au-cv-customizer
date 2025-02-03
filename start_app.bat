@echo off
start cmd /k "cd /d C:\Users\speci\CascadeProjects\au-cv-customizer && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python app.py"
start cmd /k "cd /d C:\Users\speci\CascadeProjects\au-cv-customizer\frontend-test && npm start"
