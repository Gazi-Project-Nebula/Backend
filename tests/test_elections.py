
def test_create_election(client, auth_header, monkeypatch):
    election_data = {
        "title": "Class President",
        "description": "Vote for the best",
        "start_time": "2025-01-01T09:00:00",
        "end_time": "2025-01-02T17:00:00",
        "candidates": [
            {"name": "Alice", "bio": "Hardworking"},
            {"name": "Bob", "bio": "Creative"}
        ]
    }
    
    response = client.post("/elections/", json=election_data, headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Class President"
    assert data["status"] == "pending"
    assert len(data["candidates"]) == 2
    assert data["candidates"][0]["name"] == "Alice"

def test_create_election_unauthorized(client):
    """Ensure anonymous users cannot create elections."""
    election_data = {
        "title": "Illegal Election",
        "start_time": "2025-01-01T09:00:00",
        "end_time": "2025-01-02T17:00:00",
        "candidates": []
    }
    response = client.post("/elections/", json=election_data)
    assert response.status_code == 401

import time
from datetime import datetime, timedelta
import crud

def test_election_status_change(client, auth_header, db_session):
    # Using a fixed time in the past to avoid race conditions with the scheduler
    start_time = datetime.utcnow() - timedelta(minutes=10)
    end_time = start_time + timedelta(minutes=5)

    election_data = {
        "title": "Manual Status Change Test",
        "description": "Testing direct status changes",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "candidates": [{"name": "Candidate 1", "bio": "Bio 1"}]
    }

    # Create the election
    response = client.post("/elections/", json=election_data, headers=auth_header)
    assert response.status_code == 200
    election_id = response.json()["id"]

    # Check initial status is "pending"
    response = client.get(f"/elections/{election_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

    # Manually start the election by calling the crud function
    crud.start_election(db_session, election_id=election_id)

    # Check for "active" status
    response = client.get(f"/elections/{election_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

    # Manually end the election
    crud.end_election(db_session, election_id=election_id)

    # Check for "completed" status
    response = client.get(f"/elections/{election_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

def test_create_election_no_schedule(client, auth_header):
    election_data = {
        "title": "Unscheduled Election",
        "description": "This election is not scheduled",
        "candidates": [
            {"name": "Candidate A", "bio": "Bio A"},
        ]
    }
    
    response = client.post("/elections/", json=election_data, headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Unscheduled Election"
    assert data["status"] == "pending"
    assert data["start_time"] is None
    assert data["end_time"] is None