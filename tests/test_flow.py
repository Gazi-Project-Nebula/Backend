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
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    
    if response.status_code == 200:
        print(f"User '{username}' created successfully.")
    else:
        print(f"Error creating user: {response.text}")
        return

    print("\n--- 2. LOGIN (GET JWT) ---")
    login_data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
        
    # This is the User's ID card (JWT)
    jwt_token = response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {jwt_token}"}
    print("Logged in. JWT acquired.")

    print("\n--- 3. CREATE ELECTION ---")
    election_data = {
        "title": f"Class President {unique_id}",
        "description": "Vote for your representative",
        "start_time": datetime.datetime.utcnow().isoformat(),
        "end_time": (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat(),
        "candidates": [
            {"name": "Alice", "description": "Hardworking"},
            {"name": "Bob", "description": "Smart"}
        ]
    }
    
    # We need the JWT to create an election (Authentication required)
    response = requests.post(f"{BASE_URL}/elections/", json=election_data, headers=auth_headers)
    
    if response.status_code == 200:
        election_id = response.json()["id"]
        candidate_id = response.json()["candidates"][0]["id"] # Get Alice's ID
        print(f"Election created (ID: {election_id}) with candidate Alice (ID: {candidate_id}).")
    else:
        print(f"Failed to create election: {response.text}")
        return

    print("\n--- 4. GENERATE VOTING TOKEN (The new step!) ---")
    # The user asks for a token using their JWT (proving they are eligible)
    response = requests.post(f"{BASE_URL}/elections/{election_id}/token", headers=auth_headers)
    
    if response.status_code == 200:
        voting_token = response.json()["voting_token"]
        print(f"Voting Token received: {voting_token}")
        print("(System has now recorded that this user took a token, but the token itself is anonymous)")
    else:
        print(f"Failed to get token: {response.text}")
        return

    print("\n--- 5. CAST ANONYMOUS VOTE ---")
    # Notice: We do NOT use 'auth_headers' here. The user is anonymous.
    # We only send the voting_token we just got.
    vote_data = {
        "election_id": election_id,
        "candidate_id": candidate_id,
        "token": voting_token
    }
    
    response = requests.post(f"{BASE_URL}/votes/", json=vote_data)
    
    if response.status_code == 200:
        receipt = response.json()
        print("Vote Cast Successfully!")
        print(f"Vote Receipt Hash: {receipt['vote_hash']}")
        print(f"Timestamp: {receipt['timestamp']}")
    else:
        print(f"Voting failed: {response.text}")
        
    print("\n--- 6. TRY DOUBLE VOTING (Should Fail) ---")
    response = requests.post(f"{BASE_URL}/votes/", json=vote_data)
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