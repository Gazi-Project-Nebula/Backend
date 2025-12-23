from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Annotated

from src.core.config import settings
from src.application import schemas
from src.infrastructure.database.session import get_db
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.database.models import User

# Services
from src.application.services.auth_service import AuthService
from src.application.services.election_service import ElectionService
from src.application.services.voting_service import VotingService
from src.infrastructure.repositories.election_repository import SqlAlchemyElectionRepository, SqlAlchemyCandidateRepository
from src.infrastructure.repositories.vote_repository import SqlAlchemyVoteRepository, SqlAlchemyVotingTokenRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency for DB Session
DbSession = Annotated[Session, Depends(get_db)]

def get_user_repository(db: DbSession):
    return SqlAlchemyUserRepository(db)

def get_election_repository(db: DbSession):
    return SqlAlchemyElectionRepository(db)

def get_candidate_repository(db: DbSession):
    return SqlAlchemyCandidateRepository(db)

def get_vote_repository(db: DbSession):
    return SqlAlchemyVoteRepository(db)

def get_token_repository(db: DbSession):
    return SqlAlchemyVotingTokenRepository(db)

# Service Dependencies
def get_auth_service(user_repo = Depends(get_user_repository)):
    return AuthService(user_repo)

def get_election_service(
    election_repo = Depends(get_election_repository),
    candidate_repo = Depends(get_candidate_repository),
    token_repo = Depends(get_token_repository),
    user_repo = Depends(get_user_repository)
):
    return ElectionService(election_repo, candidate_repo, token_repo, user_repo)

def get_voting_service(
    vote_repo = Depends(get_vote_repository),
    token_repo = Depends(get_token_repository)
):
    return VotingService(vote_repo, token_repo)


# Auth Dependencies
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
    
    user_repo = SqlAlchemyUserRepository(db)
    user = user_repo.get_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def verify_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Admin privileges required."
        )
    return current_user

# Helper to verify election manager (used in main.py)
# Ideally this logic belongs in the Service check, but for route protection we can keep it here.
def verify_election_manager(election_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    election_repo = SqlAlchemyElectionRepository(db)
    election = election_repo.get_by_id(election_id)
    if not election:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Election not found")
    if election.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to manage this election")
    return election
