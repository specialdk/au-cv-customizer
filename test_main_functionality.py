import requests
import json
import os
import time

BASE_URL = 'http://localhost:5000/api'

def wait_for_server(timeout=30):
    """Wait for the server to be ready."""
    print("\nWaiting for server to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get('http://localhost:5000/api/health')
            if response.status_code == 200:
                print("Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            print(".", end="", flush=True)
            time.sleep(1)
    print("\nServer did not become ready in time")
    return False

def test_auth_and_upload():
    # Wait for server to be ready
    if not wait_for_server():
        print("Cannot proceed with tests as server is not ready")
        return

    # 1. Register
    register_data = {
        'email': 'test2@example.com',
        'password': 'testpass123',
        'name': 'Test User 2'
    }
    print("\n1. Testing Registration...")
    register_response = requests.post(f'{BASE_URL}/register', json=register_data)
    print(f"Registration Status: {register_response.status_code}")
    print(f"Response: {register_response.json()}")

    # 2. Login
    login_data = {
        'email': 'test2@example.com',
        'password': 'testpass123'
    }
    print("\n2. Testing Login...")
    login_response = requests.post(f'{BASE_URL}/login', json=login_data)
    print(f"Login Status: {login_response.status_code}")
    login_result = login_response.json()
    print(f"Response: {login_result}")
    
    # Get token from response
    token = login_result.get('token')
    if not token:
        print("Failed to get access token")
        return

    # 3. Upload CV
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    print("\n3. Testing CV Upload...")
    # Create a test CV file
    with open('test_cv.txt', 'w') as f:
        f.write("Test CV Content\nSkills: Python, React\nExperience: 5 years")
    
    with open('test_cv.txt', 'rb') as f:
        files = {'file': ('test_cv.txt', f, 'text/plain')}
        upload_response = requests.post(
            f'{BASE_URL}/documents/upload',
            headers=headers,
            files=files
        )
        print(f"Upload Status: {upload_response.status_code}")
        try:
            print(f"Response: {upload_response.json()}")
        except:
            print(f"Raw Response: {upload_response.text}")

    # 4. Parse Job URL
    print("\n4. Testing Job Parsing...")
    job_data = {
        'url': 'https://www.seek.com.au/job/72729195'
    }
    job_response = requests.post(
        f'{BASE_URL}/jobs/parse',
        headers=headers,
        json=job_data
    )
    print(f"Job Parse Status: {job_response.status_code}")
    try:
        print(f"Response: {job_response.json()}")
    except:
        print(f"Raw Response: {job_response.text}")

if __name__ == '__main__':
    test_auth_and_upload()
