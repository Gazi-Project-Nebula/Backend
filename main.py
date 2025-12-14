from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

import crud, schemas, security, database
from config import settings

# Create database tables when the application starts
database.create_db_and_tables()

# --- SCHEDULER ---
scheduler = BackgroundScheduler()

def trigger_start_election(election_id: int):
    db = database.SessionLocal()
    crud.start_election(db, election_id)
    db.close()

def trigger_end_election(election_id: int):
    db = database.SessionLocal()
    crud.end_election(db, election_id)
    db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not scheduler.running:
        scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# Endpoint to create a new user 
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(security.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

# Endpoint to log in a user and get an access token
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(security.get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# NEW Endpoint: Login per requirements
# Authenticates a user and returns the User object
@app.post("/api/auth/login", response_model=schemas.User)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(security.get_db)):
    user = crud.get_user_by_username(db, username=user_credentials.username)
    if not user or not security.verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    return user

# NEW Endpoint: Register per requirements
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(security.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user.role = "voter" # Force default role to voter
    crud.create_user(db=db, user=user)
    return Response(status_code=status.HTTP_201_CREATED)

# A protected endpoint that shows information about the current logged-in user.
@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(security.get_current_user)):
    return current_user

# Endpoint to create a new election
@app.post("/api/elections", status_code=status.HTTP_201_CREATED)
def create_election(
    election_request: schemas.ElectionCreateRequest, 
    db: Session = Depends(security.get_db), 
    current_user: schemas.User = Depends(security.get_current_user)
):
    # Map the request to the internal schema expected by CRUD
    candidate_objects = [schemas.CandidateCreate(name=name) for name in election_request.candidate_names]
    
    internal_election = schemas.ElectionCreate(
        title=election_request.title,
        description=election_request.description,
        start_time=datetime.utcnow(), # Default start time to now
        end_time=election_request.end_time,
        candidates=candidate_objects
    )

    db_election = crud.create_election(db=db, election=internal_election, user_id=current_user.id)
    
    if db_election.start_time and db_election.end_time:
        scheduler.add_job(trigger_start_election, 'date', run_date=db_election.start_time, args=[db_election.id])
        scheduler.add_job(trigger_end_election, 'date', run_date=db_election.end_time, args=[db_election.id])
        
    return {"success": True, "message": "Election created and tokens distributed to all users."}

from typing import List

# NEW Endpoint: Get All Elections
@app.get("/api/elections", response_model=List[schemas.Election])
def read_elections(skip: int = 0, limit: int = 100, db: Session = Depends(security.get_db)):
    return crud.get_elections(db, skip=skip, limit=limit)
...
@app.get("/api/elections/{election_id}", response_model=schemas.Election)
def read_election(election_id: int, db: Session = Depends(security.get_db)):
    db_election = crud.get_election(db, election_id=election_id)
    if db_election is None:
        raise HTTPException(status_code=404, detail="Election not found")
    return db_election

# --- Candidate Management Endpoints ---

@app.post("/elections/{election_id}/candidates", response_model=schemas.Candidate)
def create_candidate_for_election(
    election_id: int,
    candidate: schemas.CandidateCreate,
    db: Session = Depends(security.get_db),
    election: database.Election = Depends(security.verify_election_manager)
):
    return crud.create_candidate(db=db, candidate=candidate, election_id=election_id)

@app.get("/elections/{election_id}/candidates", response_model=List[schemas.Candidate])
def read_candidates_for_election(
    election_id: int, 
    db: Session = Depends(security.get_db),
    current_user: schemas.User = Depends(security.get_current_user)
):
    return crud.get_candidates_by_election(db=db, election_id=election_id)

@app.put("/candidates/{candidate_id}", response_model=schemas.Candidate)
def update_candidate_details(
    candidate_id: int,
    candidate_update: schemas.CandidateUpdate,
    db: Session = Depends(security.get_db),
    candidate: database.Candidate = Depends(security.verify_candidate_election_manager)
):
    return crud.update_candidate(db=db, candidate_id=candidate_id, candidate=candidate_update)

from fastapi import Response
...
@app.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate_from_election(
    candidate_id: int,
    db: Session = Depends(security.get_db),
    candidate: database.Candidate = Depends(security.verify_candidate_election_manager)
):
    crud.delete_candidate(db=db, candidate_id=candidate_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# 1. Add this NEW endpoint to generate tokens
@app.post("/elections/{election_id}/token")
def generate_voting_token(election_id: int, db: Session = Depends(security.get_db), current_user: schemas.User = Depends(security.get_current_user)):
    # Verify election exists
    election = crud.get_election(db, election_id=election_id)
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")
        
    # Generate token
    token = crud.create_voting_token(db, user_id=current_user.id, election_id=election_id)
    
    if not token:
        raise HTTPException(status_code=400, detail="You have already generated a voting token for this election.")
        
    return {"voting_token": token, "message": "Save this token! You need it to vote."}

# 2. UPDATE the existing /votes/ endpoint to /api/votes
@app.post("/api/votes", status_code=status.HTTP_200_OK)
def cast_vote(vote: schemas.VoteCastRequest, db: Session = Depends(security.get_db)):
    # Check if election is active
    election = crud.get_election(db, election_id=vote.election_id)
    if not election or election.status != "active":
        raise HTTPException(status_code=400, detail="Election is not active")

    try:
        # The crud.cast_vote function now handles token validation
        db_vote = crud.cast_vote(db=db, vote=vote)
    except ValueError as e:
        # Catch errors like "Invalid token" or "Already used"
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "success": True,
        "message": "Vote successfully cast.",
        "vote_hash": db_vote.vote_hash
    }

# The main welcome endpoint.
@app.get("/")
def read_root():
    return {"message": "Welcome to the Secure E-Voting API"}