import requests
import json

def test_registration():
    url = 'http://localhost:5000/api/register'
    data = {
        'email': 'test@example.com',
        'password': 'password123'
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        print(f"Sending request to {url}")
        print(f"Headers: {headers}")
        print(f"Data: {json.dumps(data)}")
        
        response = requests.post(url, json=data, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        try:
            print(f"Response JSON: {response.json()}")
        except:
            print("Could not parse response as JSON")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    test_registration()
