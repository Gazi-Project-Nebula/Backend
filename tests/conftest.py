import pytest
import sys
import os

# Add the parent directory (Backend) to sys.path so we can import 'main' and 'src'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import main
from src.infrastructure.database.models import Base
from src.infrastructure.database.session import get_db
from apscheduler.schedulers.background import BackgroundScheduler

@pytest.fixture(scope="session")
def db_engine():
    """
    Creates a new in-memory SQLite database engine for the test session,
    creates all tables, and then drops them after the session.
    """
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Creates a new database session for each test.
    It uses a transaction that is rolled back after the test, ensuring isolation.
    """
    connection = db_engine.connect()
    # Begin a transaction
    trans = connection.begin()
    # Create a session that will use the connection's transaction
    db = Session(bind=connection)
    yield db
    # Rollback the transaction to discard any changes made during the test
    db.close()
    trans.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """
    Overrides the 'get_db' dependency to use the isolated test database session.
    Also mocks the scheduler to prevent actual job execution.
    """
    from unittest.mock import MagicMock
    import src.core.scheduler
    
    # Mock the scheduler instance
    mock_scheduler = MagicMock()
    # Ensure running property is False by default so lifespan startup logic runs if needed,
    # or just let it be a mock.
    mock_scheduler.running = False 
    
    # Save original to restore after
    original_scheduler = src.core.scheduler.scheduler
    src.core.scheduler.scheduler = mock_scheduler

    def override_get_db():
        yield db_session

    main.app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(main.app) as c:
        yield c
    
    # Cleanup
    del main.app.dependency_overrides[get_db]
    src.core.scheduler.scheduler = original_scheduler
    
@pytest.fixture
def auth_header(client):
    """Registers a default user and returns valid Authorization headers."""
    client.post("/users/", json={"username": "admin", "password": "adminpass"})
    response = client.post("/token", data={"username": "admin", "password": "adminpass"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
    