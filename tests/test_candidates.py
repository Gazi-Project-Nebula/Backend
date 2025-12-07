from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest

from schemas import UserCreate, ElectionCreate, CandidateCreate, CandidateUpdate
from crud import create_user, create_election, create_candidate
import database, security

# The client fixture is automatically used by pytest thanks to conftest.py

@pytest.fixture(scope="function")
def test_user(db_session: Session):
    user_data = UserCreate(username="testuser_candidates", password="password", role="admin")
    return create_user(db_session, user_data)

@pytest.fixture(scope="function")
def auth_header(client: TestClient, test_user):
    response = client.post("/token", data={"username": test_user.username, "password": "password"})
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def test_election(db_session: Session, test_user):
    election_data = ElectionCreate(
        title="Test Election for Candidates",
        description="An election to test candidate management",
        candidates=[]
    )
    return create_election(db_session, election_data, test_user.id)

def test_create_candidate(client: TestClient, auth_header, test_election):
    candidate_data = CandidateCreate(name="Test Candidate 1", bio="Bio 1")
    response = client.post(
        f"/elections/{test_election.id}/candidates",
        json=candidate_data.model_dump(),
        headers=auth_header
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Candidate 1"
    assert data["election_id"] == test_election.id

def test_get_candidates(client: TestClient, db_session: Session, auth_header, test_election):
    # First, create a candidate to ensure there is one
    create_candidate(db_session, CandidateCreate(name="Temp Candidate", bio=""), test_election.id)
    response = client.get(f"/elections/{test_election.id}/candidates", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

def test_update_candidate(client: TestClient, db_session: Session, auth_header, test_election):
    candidate = create_candidate(db_session, CandidateCreate(name="To be updated", bio=""), test_election.id)
    update_data = CandidateUpdate(name="Updated Test Candidate")
    response = client.put(
        f"/candidates/{candidate.id}",
        json=update_data.model_dump(exclude_unset=True),
        headers=auth_header
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Test Candidate"

def test_delete_candidate(client: TestClient, db_session: Session, auth_header, test_election):
    candidate = create_candidate(db_session, CandidateCreate(name="To be deleted", bio=""), test_election.id)
    response = client.delete(f"/candidates/{candidate.id}", headers=auth_header)
    assert response.status_code == 204
    
    # Verify the candidate is deleted
    db_candidate = db_session.query(database.Candidate).filter(database.Candidate.id == candidate.id).first()
    assert db_candidate is None

def test_unauthorized_candidate_management(client: TestClient, db_session: Session, test_election):
    # Create a new user who is not the election manager
    other_user_data = UserCreate(username="otheruser_candidates", password="password", role="voter")
    other_user = create_user(db_session, other_user_data)
    response = client.post("/token", data={"username": other_user.username, "password": "password"})
    other_auth_header = {"Authorization": f"Bearer {response.json()['access_token']}"}

    candidate_data = CandidateCreate(name="Unauthorized Candidate", bio="Bio")
    
    # Try to create a candidate
    response = client.post(
        f"/elections/{test_election.id}/candidates",
        json=candidate_data.model_dump(),
        headers=other_auth_header
    )
    assert response.status_code == 403

    # Create a candidate for the other tests
    candidate = create_candidate(db_session, CandidateCreate(name="test", bio="test"), test_election.id)

    # Try to update a candidate
    update_data = CandidateUpdate(name="Unauthorized Update")
    response = client.put(
        f"/candidates/{candidate.id}",
        json=update_data.model_dump(exclude_unset=True),
        headers=other_auth_header
    )
    assert response.status_code == 403

    # Try to delete a candidate
    response = client.delete(f"/candidates/{candidate.id}", headers=other_auth_header)
    assert response.status_code == 403
