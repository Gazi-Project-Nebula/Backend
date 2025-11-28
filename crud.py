# Contains reusable functions to interact with the database (Create, Read, Update, Delete).
import hashlib
import datetime
from sqlalchemy.orm import Session
import database, schemas
from passlib.context import CryptContext

# Sets up the password hashing scheme.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Finds a user in the database by their username.
def get_user_by_username(db: Session, username: str):
    return db.query(database.User).filter(database.User.username == username).first()

# Creates a new user in the database with a hashed password.
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = database.User(username=user.username, password_hash=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_election(db: Session, election: schemas.ElectionCreate, user_id: int):
    # 1. Create the Election object
    db_election = database.Election(
        title=election.title,
        description=election.description,
        start_time=election.start_time,
        end_time=election.end_time,
        created_by=user_id
    )
    db.add(db_election)
    db.commit()
    db.refresh(db_election)

    # 2. Create the Candidate objects linked to this election
    for candidate in election.candidates:
        db_candidate = database.Candidate(
            name=candidate.name,
            description=candidate.description,
            election_id=db_election.id
        )
        db.add(db_candidate)
    
    db.commit()
    db.refresh(db_election)
    return db_election

def get_elections(db: Session, skip: int = 0, limit: int = 100):
    # Fetch all elections to display on the dashboard
    return db.query(database.Election).offset(skip).limit(limit).all()

def get_election(db: Session, election_id: int):
    return db.query(database.Election).filter(database.Election.id == election_id).first()