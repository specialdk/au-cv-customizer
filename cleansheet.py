import os
import sys
import shutil
import argparse
import time
import requests
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def clean_database():
    """Remove the SQLite database file."""
    db_file = Path('backend/app.db')
    if db_file.exists():
        print(f"Removing database file: {db_file}")
        db_file.unlink()

def clean_uploads():
    """Clean the uploads directory."""
    uploads_dir = Path('backend/uploads')
    if uploads_dir.exists():
        print(f"Cleaning uploads directory: {uploads_dir}")
        shutil.rmtree(uploads_dir)
    uploads_dir.mkdir(exist_ok=True)

def stop_servers():
    """Stop any running Flask or npm processes."""
    # This is Windows-specific
    os.system('taskkill /f /im python.exe 2>nul')
    os.system('taskkill /f /im node.exe 2>nul')

def start_servers():
    """Start both backend and frontend servers."""
    # Start backend with proper Python path
    backend_cmd = f'cd backend && set PYTHONPATH={project_root} && python -m flask run --port=5000'
    os.system(f'start cmd /k "{backend_cmd}"')
    
    # Start frontend
    os.system('start cmd /k "cd frontend-test && npm start"')

def wait_for_servers(timeout=30):
    """Wait for servers to be ready."""
    print("\nWaiting for servers to be ready...")
    start_time = time.time()
    backend_ready = False
    frontend_ready = False
    
    while time.time() - start_time < timeout:
        if not backend_ready:
            try:
                response = requests.get('http://localhost:5000/api/health')
                if response.status_code == 200:
                    print("Backend server is ready!")
                    backend_ready = True
            except requests.exceptions.ConnectionError:
                pass
        
        if not frontend_ready:
            try:
                response = requests.get('http://localhost:3002')
                if response.status_code == 200:
                    print("Frontend server is ready!")
                    frontend_ready = True
            except requests.exceptions.ConnectionError:
                pass
        
        if backend_ready and frontend_ready:
            return True
        
        print(".", end="", flush=True)
        time.sleep(1)
    
    print("\nTimeout waiting for servers")
    return False

def cleansheet(mode='blank'):
    """
    Prepare the environment for testing.
    
    Args:
        mode (str): Either 'blank' for fresh start or 'retain' to keep data
    """
    print(f"\nInitiating CLEANSHEET ({mode.upper()}) setup...")
    
    # Always stop existing servers
    print("\nStopping any running servers...")
    stop_servers()
    
    if mode == 'blank':
        # Clean everything for a fresh start
        print("\nCleaning database...")
        clean_database()
        
        print("\nCleaning uploads directory...")
        clean_uploads()
    
    # Start servers
    print("\nStarting servers...")
    start_servers()
    
    # Wait for servers
    if wait_for_servers():
        print("\nCLEANSHEET setup complete!")
        print("\nServers are available at:")
        print("- Backend: http://localhost:5000")
        print("- Frontend: http://localhost:3002")
    else:
        print("\nWarning: Servers may not be fully ready")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare testing environment')
    parser.add_argument('mode', choices=['blank', 'retain'], 
                       help='blank for fresh start, retain to keep existing data')
    args = parser.parse_args()
    
    cleansheet(args.mode)
