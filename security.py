# Manages all security-related logic, like password hashing and user authentication
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

import schemas, crud
from database import SessionLocal
from config import settings

# Context for hashing and verifying passwords using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Defines the OAuth2 security scheme, which specifies how to get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Checks if a plain password matches a hashed password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Creates a new JSON Web Token (JWT) for a user.
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# A dependency to get a database session for a single request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Decodes a JWT token to get the current user. This protects endpoints
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def verify_election_manager(election_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    election = crud.get_election(db, election_id)
    if not election:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Election not found")
    if election.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to manage this election")
    return election

def verify_candidate_election_manager(candidate_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    candidate = crud.get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    
    election = crud.get_election(db, candidate.election_id)
    if not election:
        # This case should ideally not happen if database integrity is maintained
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Election not found for this candidate")
        
    if election.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to manage this election's candidates")
    return candidate
