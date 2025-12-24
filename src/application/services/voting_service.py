from typing import Optional
import hashlib
import datetime
import secrets
from src.domain.interfaces import IVoteRepository, IVotingTokenRepository, IElectionRepository
from src.infrastructure.database.models import Vote, VotingToken
from src.application import schemas

class VotingService:
    def __init__(self, vote_repo: IVoteRepository, token_repo: IVotingTokenRepository, election_repo: IElectionRepository):
        self.vote_repo = vote_repo
        self.token_repo = token_repo
        self.election_repo = election_repo

    def generate_token(self, user_id: int, election_id: int):
        existing_token = self.token_repo.get_token(user_id, election_id)
        if existing_token:
            return None
        
        raw_token = secrets.token_urlsafe(16)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        
        self.token_repo.create_token(
            token_hash=hashed_token,
            user_id=user_id,
            election_id=election_id,
            expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        )
        return raw_token

    def cast_vote(self, vote_req: schemas.VoteCastRequest):
        # 0. Validate Election Status
        election = self.election_repo.get_by_id(vote_req.election_id)
        if not election:
            raise ValueError("Election not found.")
        if election.status != "active":
            raise ValueError(f"Election is not active. Current status: {election.status}")

        # 1. Validate Token
        db_token = self.token_repo.get_token(vote_req.user_id, vote_req.election_id)
        if not db_token:
            raise ValueError("Voting token not found for this user and election.")
        if db_token.is_used:
            raise ValueError("Double Vote: This token has already been used.")
        
        # Check expiry (naive vs aware handling required if not standardized)
        # Using database.models.AwareDateTime, db_token.expires_at should be aware.
        if db_token.expires_at < datetime.datetime.now(datetime.timezone.utc):
             raise ValueError("Token has expired.")

        # 2. Mark Token Used
        # Note: Ideally this should be atomic with vote creation.
        # Here we rely on the repository implementation.
        self.token_repo.mark_as_used(db_token)

        # 3. Blockchain Logic
        last_vote = self.vote_repo.get_last_vote(vote_req.election_id)
        prev_hash = last_vote.vote_hash if last_vote else "GENESIS"
        
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        data_to_hash = f"{prev_hash}{vote_req.user_id}{vote_req.candidate_id}{timestamp}"
        vote_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()

        new_vote = Vote(
            vote_hash=vote_hash,
            prev_vote_hash=prev_hash,
            election_id=vote_req.election_id,
            candidate_id=vote_req.candidate_id,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        return self.vote_repo.create(new_vote)

    def get_results(self, election_id: int):
        return self.vote_repo.get_results(election_id)
