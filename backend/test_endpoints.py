import requests
import json
import os
import tempfile

BASE_URL = 'http://localhost:5000/api'

def test_health():
    response = requests.get(f'{BASE_URL}/health')
    print('\nHealth Check:')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')

def test_register():
    data = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test User'
    }
    response = requests.post(f'{BASE_URL}/register', json=data)
    print('\nRegister:')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    return response.json().get('access_token')

def test_login():
    data = {
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    response = requests.post(f'{BASE_URL}/login', json=data)
    print('\nLogin:')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    return response.json().get('access_token')

def test_protected_route(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/user', headers=headers)
    print('\nGet User Profile:')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')

def test_upload_document(token):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write('This is a test CV file.')
        test_file_path = temp_file.name
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            response = requests.post(f'{BASE_URL}/documents/upload', headers=headers, files=files)
        
        print('\nUpload Document:')
        print(f'Status: {response.status_code}')
        print(f'Response: {response.json()}')
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(test_file_path)
        except Exception as e:
            print(f'Warning: Could not delete temporary file: {e}')

def test_get_documents(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/documents', headers=headers)
    print('\nGet Documents:')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')

if __name__ == '__main__':
    print('Starting API Tests...')
    
    # Test health endpoint
    test_health()
    
    # Test registration
    token = test_register()
    
    # Test login
    if not token:
        token = test_login()
    
    # Test protected route
    if token:
        test_protected_route(token)
        test_upload_document(token)
        test_get_documents(token)
    
    print('\nTests completed!')
