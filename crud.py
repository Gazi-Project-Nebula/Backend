# Contains reusable functions to interact with the database (Create, Read, Update, Delete).
import hashlib
import datetime
import secrets
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
import database, schemas
from passlib.context import CryptContext

# Sets up the password hashing scheme.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Finds a user in the database by their username.
def get_user_by_username(db: Session, username: str):
    return db.query(database.User).filter(database.User.username == username).first()


def get_user(db: Session, user_id: int):
    return db.query(database.User).filter(database.User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(database.User).offset(skip).limit(limit).all()


def update_user_role(db: Session, user_id: int, role: str):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.role = role
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user



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
    
    # 3. Generate Voting Tokens for ALL users (Requirement: Token System)
    # Admin seçim oluşturduğunda, her kullanıcı için otomatik token üretilir.
    users = db.query(database.User).all()
    for user in users:
        raw_token = secrets.token_urlsafe(16)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        db_token = database.VotingToken(
            token_hash=hashed_token,
            election_id=db_election.id,
            user_id=user.id,
            expires_at=election.end_time if election.end_time else datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        )
        db.add(db_token)
    
    db.commit()
    db.refresh(db_election)
    return db_election

def get_elections(db: Session, skip: int = 0, limit: int = 100):
    # Fetch all elections to display on the dashboard
    # Requirement: Must return candidates as a nested array
    return db.query(database.Election).options(joinedload(database.Election.candidates)).offset(skip).limit(limit).all()

def get_election(db: Session, election_id: int):
    return db.query(database.Election).options(joinedload(database.Election.candidates)).filter(database.Election.id == election_id).first()

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
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    )
    db.add(db_token)
    db.commit()
    
    return raw_token

# --- UPDATED VOTING FUNCTION ---

def cast_vote(db: Session, vote: schemas.VoteCastRequest):
    # 1. Validate Token: Query voting_tokens where user_id = ? AND election_id = ?
    db_token = db.query(database.VotingToken).filter(
        database.VotingToken.user_id == vote.user_id,
        database.VotingToken.election_id == vote.election_id
    ).first()

    if not db_token:
        raise ValueError("Voting token not found for this user and election.")
    if db_token.is_used:
        raise ValueError("Double Vote: This token has already been used.")
    if db_token.expires_at < datetime.datetime.now(datetime.timezone.utc):
        raise ValueError("Token has expired.")

    # 2. Mark token as used (Burn Token)
    db_token.is_used = True
    db.add(db_token) # Stage the update

    # 3. Blockchain Logic (Get Previous Hash)
    last_vote = db.query(database.Vote).filter(
        database.Vote.election_id == vote.election_id
    ).order_by(desc(database.Vote.id)).first()

    if last_vote:
        prev_hash = last_vote.vote_hash
    else:
        # Requirement: Genesis hash for the first vote
        prev_hash = "GENESIS"

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # 4. Create Hash: SHA256(prev_hash + user_id + candidate_id + timestamp)
    data_to_hash = f"{prev_hash}{vote.user_id}{vote.candidate_id}{timestamp}"
    vote_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()

    # 5. Commit Vote
    db_vote = database.Vote(
        vote_hash=vote_hash,
        prev_vote_hash=prev_hash,
        election_id=vote.election_id,
        candidate_id=vote.candidate_id,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(db_vote)
    
    # 6. Commit both changes together (Atomic Transaction)
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


def update_election(db: Session, election_id: int, election: schemas.ElectionUpdate):
    db_election = get_election(db, election_id)
    if db_election:
        update_data = election.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_election, key, value)
        db.commit()
        db.refresh(db_election)
    return db_election


def delete_election(db: Session, election_id: int):
    db_election = get_election(db, election_id)
    if db_election:
        db.delete(db_election)
        db.commit()
    return db_election

def create_candidate(db: Session, candidate: schemas.CandidateCreate, election_id: int):
    db_candidate = database.Candidate(**candidate.model_dump(), election_id=election_id)
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def get_candidates_by_election(db: Session, election_id: int):
    return db.query(database.Candidate).filter(database.Candidate.election_id == election_id).all()

def get_candidate(db: Session, candidate_id: int):
    return db.query(database.Candidate).filter(database.Candidate.id == candidate_id).first()

def update_candidate(db: Session, candidate_id: int, candidate: schemas.CandidateUpdate):
    db_candidate = get_candidate(db, candidate_id)
    if db_candidate:
        update_data = candidate.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_candidate, key, value)
        db.commit()
        db.refresh(db_candidate)
    return db_candidate

def delete_candidate(db: Session, candidate_id: int):
    db_candidate = get_candidate(db, candidate_id)
    if db_candidate:
        db.delete(db_candidate)
        db.commit()
    return None

def get_election_results(db: Session, election_id: int):
    """
    Calculates the results of a given election by counting votes for each candidate.
    """
    from sqlalchemy import func

    # Query to count votes for each candidate in the specified election
    results = (
        db.query(
            database.Candidate.id,
            database.Candidate.name,
            func.count(database.Vote.id).label("vote_count"),
        )
        .outerjoin(database.Vote, database.Candidate.id == database.Vote.candidate_id)
        .filter(database.Candidate.election_id == election_id)
        .group_by(database.Candidate.id, database.Candidate.name)
        .order_by(func.count(database.Vote.id).desc())
        .all()
    )

    # Format the results into the desired dictionary structure
    return [
        {"id": r.id, "name": r.name, "vote_count": r.vote_count} for r in results
    ]