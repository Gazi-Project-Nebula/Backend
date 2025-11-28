from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

import crud, schemas, security, database
from config import settings

# Create database tables when the application starts
database.create_db_and_tables()


app = FastAPI()

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

# A protected endpoint that shows information about the current logged-in user.
@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(security.get_current_user)):
    return current_user

# Endpoint to create a new election
@app.post("/elections/", response_model=schemas.Election)
def create_election(election: schemas.ElectionCreate, db: Session = Depends(security.get_db), current_user: schemas.User = Depends(security.get_current_user)):
    return crud.create_election(db=db, election=election, user_id=current_user.id)

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

# 2. UPDATE the existing /votes/ endpoint
# REMOVE "current_user" dependency. The token proves permission now.
@app.post("/votes/", response_model=schemas.VoteReceipt)
def cast_vote(vote: schemas.VoteCreate, db: Session = Depends(security.get_db)):
    # Check if election is active
    election = crud.get_election(db, election_id=vote.election_id)
    if not election or not election.is_active:
        raise HTTPException(status_code=400, detail="Election is not active")

    try:
        # The crud.cast_vote function now handles token validation
        db_vote = crud.cast_vote(db=db, vote=vote)
    except ValueError as e:
        # Catch errors like "Invalid token" or "Already used"
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"vote_hash": db_vote.vote_hash, "timestamp": db_vote.created_at}

# The main welcome endpoint.
@app.get("/")
def read_root():
    return {"message": "Welcome to the Secure E-Voting API"}