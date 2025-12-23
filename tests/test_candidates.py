from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest

from src.application.schemas import UserCreate, ElectionCreate, CandidateCreate, CandidateUpdate, ElectionCreateRequest
from src.infrastructure.database import models as database
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.repositories.election_repository import SqlAlchemyElectionRepository, SqlAlchemyCandidateRepository
from src.infrastructure.security import utils as security

# The client fixture is automatically used by pytest thanks to conftest.py

@pytest.fixture(scope="function")
def test_user(db_session: Session):
    user_repo = SqlAlchemyUserRepository(db_session)
    hashed = security.get_password_hash("password")
    user = database.User(username="testuser_candidates", password_hash=hashed, role="admin")
    return user_repo.create(user)

@pytest.fixture(scope="function")
def auth_header(client: TestClient, test_user):
    # We can get token directly or use the endpoint
    # Let's use the endpoint to verify full flow, or utils for speed.
    # Endpoint requires plain password 'password' which we used.
    response = client.post("/token", data={"username": test_user.username, "password": "password"})
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def test_election(db_session: Session, test_user):
    election_repo = SqlAlchemyElectionRepository(db_session)
    # The new ElectionCreate schema expects 'candidates' list
    election_data = database.Election(
        title="Test Election for Candidates",
        description="An election to test candidate management",
        created_by=test_user.id
    )
    return election_repo.create(election_data)

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
    cand_repo = SqlAlchemyCandidateRepository(db_session)
    cand_repo.create(database.Candidate(name="Temp Candidate", bio="", election_id=test_election.id))
    
    response = client.get(f"/elections/{test_election.id}/candidates", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

def test_update_candidate(client: TestClient, db_session: Session, auth_header, test_election):
    cand_repo = SqlAlchemyCandidateRepository(db_session)
    candidate = cand_repo.create(database.Candidate(name="To be updated", bio="", election_id=test_election.id))
    
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
    cand_repo = SqlAlchemyCandidateRepository(db_session)
    candidate = cand_repo.create(database.Candidate(name="To be deleted", bio="", election_id=test_election.id))
    
    response = client.delete(f"/candidates/{candidate.id}", headers=auth_header)
    assert response.status_code == 204
    
    # Verify the candidate is deleted
    db_candidate = cand_repo.get_by_id(candidate.id)
    assert db_candidate is None

def test_unauthorized_candidate_management(client: TestClient, db_session: Session, test_election):
    # Create a new user who is not the election manager
    user_repo = SqlAlchemyUserRepository(db_session)
    hashed = security.get_password_hash("password")
    other_user = user_repo.create(database.User(username="otheruser_candidates", password_hash=hashed, role="voter"))
    
    response = client.post("/token", data={"username": other_user.username, "password": "password"})
    other_auth_header = {"Authorization": f"Bearer {response.json()['access_token']}"}

    candidate_data = CandidateCreate(name="Unauthorized Candidate", bio="Bio")
    
    # Try to create a candidate
    response = client.post(
        f"/elections/{test_election.id}/candidates",
        json=candidate_data.model_dump(),
        headers=other_auth_header
    )
    # The main logic uses `verify_election_manager` which checks if current user created the election.
    # test_election was created by test_user, not other_user.
    assert response.status_code == 403

    # Create a candidate for the other tests
    cand_repo = SqlAlchemyCandidateRepository(db_session)
    candidate = cand_repo.create(database.Candidate(name="test", bio="test", election_id=test_election.id))

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
