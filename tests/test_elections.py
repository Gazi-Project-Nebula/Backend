import database

def test_create_election(client, auth_header, monkeypatch):
    election_data = {
        "title": "Class President",
        "description": "Vote for the best",
        "end_time": "2025-01-02T17:00:00",
        "candidate_names": ["Alice", "Bob"],
        "creator_id": 1
    }
    
    response = client.post("/api/elections", json=election_data, headers=auth_header)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "Election created" in data["message"]

def test_create_election_unauthorized(client):
    """Ensure anonymous users cannot create elections."""
    election_data = {
        "title": "Illegal Election",
        "end_time": "2025-01-02T17:00:00",
        "candidate_names": []
    }
    response = client.post("/api/elections", json=election_data)
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
        "end_time": end_time.isoformat(),
        "candidate_names": ["Candidate 1"]
    }

    # Create the election
    response = client.post("/api/elections", json=election_data, headers=auth_header)
    assert response.status_code == 201
    
    # Fetch ID from DB since API doesn't return it anymore
    election = db_session.query(database.Election).filter(database.Election.title == "Manual Status Change Test").first()
    election_id = election.id

    # Check initial status is "pending"
    response = client.get(f"/api/elections/{election_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

    # Manually start the election by calling the crud function
    crud.start_election(db_session, election_id=election_id)

    # Check for "active" status
    response = client.get(f"/api/elections/{election_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

    # Manually end the election
    crud.end_election(db_session, election_id=election_id)

    # Check for "completed" status
    response = client.get(f"/api/elections/{election_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

def test_create_election_no_schedule(client, auth_header):
    election_data = {
        "title": "Unscheduled Election",
        "description": "This election is not scheduled",
        "candidate_names": ["Candidate A"]
    }
    
    response = client.post("/api/elections", json=election_data, headers=auth_header)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True