import requests
import datetime

# Base URL of your API
BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("--- 1. REGISTER USER ---")
    user_data = {"username": "testuser", "password": "securepassword123"}
    # Note: We use a unique username if rerunning, or handle 400 error
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    if response.status_code == 200:
        print("User created successfully.")
    elif response.status_code == 400:
        print("User already exists (skipping creation).")
    else:
        print(f"Error creating user: {response.text}")
        return

    print("\n--- 2. LOGIN (GET TOKEN) ---")
    # OAuth2 expects form data, not JSON
    login_data = {"username": "testuser", "password": "securepassword123"}
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in. Token acquired.")

    print("\n--- 3. CREATE ELECTION ---")
    election_data = {
        "title": "Class President 2025",
        "description": "Vote for your representative",
        "start_time": datetime.datetime.utcnow().isoformat(),
        "end_time": (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat(),
        "candidates": [
            {"name": "Alice", "description": "Hardworking"},
            {"name": "Bob", "description": "Smart"}
        ]
    }
    response = requests.post(f"{BASE_URL}/elections/", json=election_data, headers=headers)
    if response.status_code == 200:
        election_id = response.json()["id"]
        candidate_id = response.json()["candidates"][0]["id"] # Get Alice's ID
        print(f"Election created (ID: {election_id}) with candidate Alice (ID: {candidate_id}).")
    else:
        print(f"Failed to create election: {response.text}")
        return

    print("\n--- 4. CAST VOTE ---")
    vote_data = {
        "election_id": election_id,
        "candidate_id": candidate_id
    }
    response = requests.post(f"{BASE_URL}/votes/", json=vote_data, headers=headers)
    if response.status_code == 200:
        receipt = response.json()
        print("Vote Cast Successfully!")
        print(f"Vote Receipt Hash: {receipt['vote_hash']}")
    else:
        print(f"Voting failed: {response.text}")

if __name__ == "__main__":
    # Ensure requests is installed: pip install requests
    try:
        run_test()
    except ImportError:
        print("Please run: pip install requests")
    except Exception as e:
        print(f"Connection failed. Is the server running? Error: {e}")