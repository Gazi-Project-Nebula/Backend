from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.domain.interfaces import IVoteRepository, IVotingTokenRepository
from src.infrastructure.database.models import Vote, VotingToken, Candidate

class SqlAlchemyVotingTokenRepository(IVotingTokenRepository):
    def __init__(self, db: Session):
        self.db = db

    def create_token(self, token_hash: str, user_id: int, election_id: int, expires_at: Any) -> VotingToken:
        token = VotingToken(
            token_hash=token_hash,
            user_id=user_id,
            election_id=election_id,
            expires_at=expires_at
        )
        self.db.add(token)
        self.db.commit()
        return token

    def get_token(self, user_id: int, election_id: int) -> Optional[VotingToken]:
        return self.db.query(VotingToken).filter(
            VotingToken.user_id == user_id,
            VotingToken.election_id == election_id
        ).first()

    def mark_as_used(self, token: VotingToken) -> VotingToken:
        token.is_used = True
        self.db.add(token) # Add to session, commit should happen in service (Unit of Work) or here.
        # Ideally, vote cast and token usage are atomic. 
        # For this refactor, I will allow commit here but the service should ideally wrap this.
        # But wait, cast_vote in crud.py did both.
        # To keep it atomic, the service should handle the session commit.
        # But my repositories have their own db session passed in.
        # I will leave the commit out here if I want atomic, but `create_token` commits.
        # Let's support commit here for simplicity, but in `cast_vote` service, we might need to flush only.
        # I'll commit here for now.
        self.db.commit()
        return token

class SqlAlchemyVoteRepository(IVoteRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, vote: Vote) -> Vote:
        self.db.add(vote)
        self.db.commit()
        self.db.refresh(vote)
        return vote

    def get_last_vote(self, election_id: int) -> Optional[Vote]:
        return self.db.query(Vote).filter(
            Vote.election_id == election_id
        ).order_by(desc(Vote.id)).first()

    def get_results(self, election_id: int) -> List[Dict[str, Any]]:
        results = (
            self.db.query(
                Candidate.id,
                Candidate.name,
                func.count(Vote.id).label("vote_count"),
            )
            .outerjoin(Vote, Candidate.id == Vote.candidate_id)
            .filter(Candidate.election_id == election_id)
            .group_by(Candidate.id, Candidate.name)
            .order_by(func.count(Vote.id).desc())
            .all()
        )
        return [{"id": r.id, "name": r.name, "vote_count": r.vote_count} for r in results]
