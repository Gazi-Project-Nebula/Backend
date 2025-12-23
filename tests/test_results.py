import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.database.models import Base
from src.infrastructure.database.session import get_db
from main import app
from src.application import schemas
from src.infrastructure.security import utils as security
from src.core.config import settings
from datetime import datetime, timedelta, timezone

# Repositories & Services
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.repositories.election_repository import SqlAlchemyElectionRepository, SqlAlchemyCandidateRepository
from src.infrastructure.repositories.vote_repository import SqlAlchemyVotingTokenRepository, SqlAlchemyVoteRepository
from src.application.services.election_service import ElectionService
from src.application.services.voting_service import VotingService

# --- Test Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_results.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the test database
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --- Fixtures ---
@pytest.fixture(scope="function")
def db_session():
    # Clean up the database before tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # Override the get_db dependency to use this session for the API calls
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    
    try:
        yield db
    finally:
        db.close()
        # Clear the override after the test is done
        app.dependency_overrides.clear()

def create_test_user(db, username, password):
    user_repo = SqlAlchemyUserRepository(db)
    hashed = security.get_password_hash(password)
    from src.infrastructure.database.models import User
    user = User(username=username, password_hash=hashed, role="voter")
    return user_repo.create(user)

@pytest.fixture(scope="function")
def test_user(db_session):
    return create_test_user(db_session, "testresultsuser", "password123")

@pytest.fixture(scope="function")
def auth_headers(test_user):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": test_user.username}, expires_delta=access_token_expires
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def completed_election_with_votes(db_session, test_user):
    # 1. Create users who will vote
    voter1 = create_test_user(db_session, "voter1", "password")
    voter2 = create_test_user(db_session, "voter2", "password")
    voter3 = create_test_user(db_session, "voter3", "password")

    # 2. Create an election using Service (to handle token generation etc)
    election_req = schemas.ElectionCreateRequest(
        title="Results Test Election",
        description="An election to test results.",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
        candidate_names=["Candidate A", "Candidate B"]
    )
    election_internal = schemas.ElectionCreate(
        title=election_req.title, description=election_req.description,
        start_time=datetime.now(timezone.utc), end_time=election_req.end_time,
        candidates=[schemas.CandidateCreate(name=name) for name in election_req.candidate_names]
    )
    
    # Init service dependencies
    e_repo = SqlAlchemyElectionRepository(db_session)
    c_repo = SqlAlchemyCandidateRepository(db_session)
    t_repo = SqlAlchemyVotingTokenRepository(db_session)
    u_repo = SqlAlchemyUserRepository(db_session)
    v_repo = SqlAlchemyVoteRepository(db_session)
    
    election_service = ElectionService(e_repo, c_repo, t_repo, u_repo)
    voting_service = VotingService(v_repo, t_repo)
    
    election = election_service.create_election(election_data=election_internal, user_id=test_user.id)
    
    # 3. Manually activate and then cast votes
    election.status = "active"
    db_session.commit() # Commit status change

    candidate_a = election.candidates[0]
    candidate_b = election.candidates[1]

    # Vote: 2 for Candidate A, 1 for Candidate B
    # Use Service to cast vote (handles token burning, hashing)
    voting_service.cast_vote(schemas.VoteCastRequest(election_id=election.id, candidate_id=candidate_a.id, user_id=voter1.id))
    voting_service.cast_vote(schemas.VoteCastRequest(election_id=election.id, candidate_id=candidate_a.id, user_id=voter2.id))
    voting_service.cast_vote(schemas.VoteCastRequest(election_id=election.id, candidate_id=candidate_b.id, user_id=voter3.id))

    # 4. Mark election as completed
    election.status = "completed"
    db_session.commit()
    db_session.refresh(election)
    return election

# --- Tests ---

def test_get_election_results_success(completed_election_with_votes, auth_headers):
    """
    Tests successful retrieval of election results for a completed election.
    """
    election_id = completed_election_with_votes.id
    
    response = client.get(f"/api/elections/{election_id}/results", headers=auth_headers)
    
    # Depending on route implementation (v1/vote_router), results might be under 'results' key or list.
    # We implemented GET .../results returning ElectionResult schema which has 'results' list.
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == election_id
    assert data["title"] == "Results Test Election"
    assert data["status"] == "completed"
    
    results = data["results"]
    assert len(results) == 2
    
    # Check if results are sorted by vote count
    assert results[0]["name"] == "Candidate A"
    assert results[0]["vote_count"] == 2
    
    assert results[1]["name"] == "Candidate B"
    assert results[1]["vote_count"] == 1

def test_get_results_for_nonexistent_election(auth_headers):
    """
    Tests that a 404 is returned for a non-existent election ID.
    """
    response = client.get("/api/elections/999/results", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Election not found"

def test_get_results_requires_auth():
    """
    Tests that the endpoint is protected and requires authentication.
    """
    response = client.get("/api/elections/1/results")
    assert response.status_code == 401 # Unauthorized