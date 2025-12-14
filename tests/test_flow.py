import requests
import datetime
import sys

# Base URL of your API
BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("--- 1. REGISTER USER ---")
    # We use a timestamp to make the username unique every time we run the test
    # so we don't get "User already exists" errors.
    unique_id = int(datetime.datetime.now().timestamp())
    username = f"voter_{unique_id}"
    password = "securepassword123"
    
    user_data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    
    if response.status_code == 201:
        print(f"User '{username}' created successfully.")
    else:
        print(f"Error creating user: {response.text}")
        return

    print("\n--- 2. LOGIN (GET USER ID & JWT) ---")
    login_data = {"username": username, "password": password}
    
    # 2a. Login to get User ID (Frontend Requirement)
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        user_id = response.json()["id"]
        print(f"User authenticated via API. User ID: {user_id}")
    else:
        print(f"API Login failed: {response.text}")
        return

    # 2b. Get JWT for Admin Actions (Creating Election)
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    if response.status_code != 200:
        print(f"Token retrieval failed: {response.text}")
        return
        
    jwt_token = response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {jwt_token}"}
    print("JWT acquired for admin actions.")

    print("\n--- 3. CREATE ELECTION ---")
    election_data = {
        "title": f"Class President {unique_id}",
        "description": "Vote for your representative",
        "start_time": datetime.datetime.utcnow().isoformat(),
        "end_time": (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat(),
        "candidate_names": ["Alice", "Bob"]
    }
    
    # We need the JWT to create an election (Authentication required)
    response = requests.post(f"{BASE_URL}/api/elections", json=election_data, headers=auth_headers)
    
    if response.status_code == 201:
        print("Election created successfully. Tokens automatically distributed.")
        # Since API doesn't return ID anymore, we assume ID=1 for this fresh test or fetch it
        # For this script, let's fetch all elections to find the ID
        list_resp = requests.get(f"{BASE_URL}/api/elections")
        latest_election = list_resp.json()[-1]
        election_id = latest_election["id"]
        candidate_id = latest_election["candidates"][0]["id"]
        print(f"Election ID: {election_id}, Candidate ID: {candidate_id}")
    else:
        print(f"Failed to create election: {response.text}")
        return

    print("\n--- 4. CAST VOTE ---")
    vote_data = {
        "election_id": election_id,
        "candidate_id": candidate_id,
        "user_id": user_id
    }
    
    response = requests.post(f"{BASE_URL}/api/votes", json=vote_data)
    
    if response.status_code == 200:
        receipt = response.json()
        print(f"Vote Cast Successfully! Message: {receipt['message']}")
        print(f"Vote Receipt Hash: {receipt['vote_hash']}")
    else:
        print(f"Voting failed: {response.text}")
        
    print("\n--- 5. TRY DOUBLE VOTING (Should Fail) ---")
    response = requests.post(f"{BASE_URL}/api/votes", json=vote_data)
    if response.status_code != 200:
        print(f"Success! Double voting prevented. Error: {response.json()['detail']}")
    else:
        print("FAIL! System allowed double voting!")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your server is running: uvicorn main:app --reload")