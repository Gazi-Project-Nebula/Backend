from typing import List, Dict, Any, Optional
import hashlib
import datetime
import secrets
from src.domain.interfaces import IElectionRepository, ICandidateRepository, IVotingTokenRepository, IUserRepository
from src.infrastructure.database.models import Election, Candidate, VotingToken
from src.application import schemas

class ElectionService:
    def __init__(self, election_repo: IElectionRepository, candidate_repo: ICandidateRepository, token_repo: IVotingTokenRepository, user_repo: IUserRepository):
        self.election_repo = election_repo
        self.candidate_repo = candidate_repo
        self.token_repo = token_repo
        self.user_repo = user_repo

    def create_election(self, election_data: schemas.ElectionCreate, user_id: int):
        # 1. Create Election
        new_election = Election(
            title=election_data.title,
            description=election_data.description,
            start_time=election_data.start_time,
            end_time=election_data.end_time,
            created_by=user_id
        )
        created_election = self.election_repo.create(new_election)

        # 2. Create Candidates
        for candidate in election_data.candidates:
            new_candidate = Candidate(
                name=candidate.name,
                bio=candidate.bio,
                election_id=created_election.id
            )
            self.candidate_repo.create(new_candidate)
        
        # 3. Generate Tokens for ALL users
        users = self.user_repo.get_all()
        for user in users:
            raw_token = secrets.token_urlsafe(16)
            hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
            # Requirement: Tokens expire when election ends or in 24h
            expires = election_data.end_time if election_data.end_time else datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
            
            self.token_repo.create_token(
                token_hash=hashed_token,
                user_id=user.id,
                election_id=created_election.id,
                expires_at=expires
            )
        
        return created_election

    def get_elections(self, skip: int = 0, limit: int = 100):
        return self.election_repo.get_all(skip, limit)

    def get_election(self, election_id: int):
        return self.election_repo.get_by_id(election_id)
    
    def start_election(self, election_id: int):
        return self.election_repo.start_election(election_id)
    
    def end_election(self, election_id: int):
        return self.election_repo.end_election(election_id)
    
    def delete_election(self, election_id: int):
        return self.election_repo.delete(election_id)
