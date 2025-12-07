def test_create_election(client, auth_header):
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