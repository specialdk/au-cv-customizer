import requests
import json
import os

BASE_URL = 'http://localhost:5000/api'

def test_auth_and_upload():
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
        'url': 'https://www.seek.com.au/job/72729195'  # Real job posting
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
