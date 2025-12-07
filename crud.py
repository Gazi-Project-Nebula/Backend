# Contains reusable functions to interact with the database (Create, Read, Update, Delete).
import hashlib
import datetime
import secrets
from sqlalchemy import desc
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
            bio=candidate.bio,
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

def create_voting_token(db: Session, user_id: int, election_id: int):
    # 1. Check if user already has a token (Prevent double voting requests)
    existing_token = db.query(database.VotingToken).filter(
        database.VotingToken.user_id == user_id,
        database.VotingToken.election_id == election_id
    ).first()
    
    if existing_token:
        return None # User already has a token

    # 2. Generate a secure random token (The "Secret Key" for the voter)
    raw_token = secrets.token_urlsafe(16)
    
    # 3. Hash it for storage. 
    # We store the hash so even if the DB is hacked, the attacker can't use the tokens.
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # 4. Save to DB linked to the user (so we know they took one)
    db_token = database.VotingToken(
        token_hash=hashed_token,
        election_id=election_id,
        user_id=user_id,
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    )
    db.add(db_token)
    db.commit()
    
    return raw_token

# --- UPDATED VOTING FUNCTION ---

def cast_vote(db: Session, vote: schemas.VoteCreate):
    # 1. Hash the incoming token to match it against the database
    token_hash = hashlib.sha256(vote.token.encode()).hexdigest()
    
    # 2. Find the token in the DB
    db_token = db.query(database.VotingToken).filter(
        database.VotingToken.token_hash == token_hash,
        database.VotingToken.election_id == vote.election_id
    ).first()

    # 3. Validate Token
    if not db_token:
        raise ValueError("Invalid voting token.")
    if db_token.is_used:
        raise ValueError("This token has already been used.")
    if db_token.expires_at < datetime.datetime.utcnow():
        raise ValueError("Token has expired.")

    # 4. Mark token as used (This prevents double voting!)
    db_token.is_used = True
    db.add(db_token) # Stage the update

    # 5. Create the Vote (Same hash-chain logic as before)
    last_vote = db.query(database.Vote).filter(
        database.Vote.election_id == vote.election_id
    ).order_by(desc(database.Vote.id)).first()

    if last_vote:
        prev_hash = last_vote.vote_hash
    else:
        prev_hash = hashlib.sha256(str(vote.election_id).encode()).hexdigest()

    timestamp = datetime.datetime.utcnow().isoformat()
    # Note: We do NOT include user_id in the hash. The vote is anonymous.
    data_to_hash = f"{prev_hash}{vote.candidate_id}{vote.election_id}{timestamp}"
    vote_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()

    db_vote = database.Vote(
        vote_hash=vote_hash,
        prev_vote_hash=prev_hash,
        election_id=vote.election_id,
        candidate_id=vote.candidate_id,
        created_at=datetime.datetime.utcnow()
    )
    db.add(db_vote)
    
    # 6. Commit both the "Token Used" and "Vote Cast" changes together (Atomic Transaction)
    db.commit()
    db.refresh(db_vote)
    
    return db_vote

def start_election(db: Session, election_id: int):
    db_election = get_election(db, election_id)
    if db_election:
        db_election.status = "active"
        db.commit()
        db.refresh(db_election)
    return db_election

def end_election(db: Session, election_id: int):
    db_election = get_election(db, election_id)
    if db_election:
        db_election.status = "completed"
        db.commit()
        db.refresh(db_election)
    return db_election