from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from src.domain.interfaces import IElectionRepository, ICandidateRepository
from src.infrastructure.database.models import Election, Candidate

class SqlAlchemyElectionRepository(IElectionRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, election: Election) -> Election:
        self.db.add(election)
        self.db.commit()
        self.db.refresh(election)
        return election

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Election]:
        return self.db.query(Election).options(joinedload(Election.candidates)).offset(skip).limit(limit).all()

    def get_by_id(self, election_id: int) -> Optional[Election]:
        return self.db.query(Election).options(joinedload(Election.candidates)).filter(Election.id == election_id).first()

    def update(self, election_id: int, update_data: Dict[str, Any]) -> Optional[Election]:
        election = self.get_by_id(election_id)
        if election:
            for key, value in update_data.items():
                setattr(election, key, value)
            self.db.commit()
            self.db.refresh(election)
        return election

    def delete(self, election_id: int) -> None:
        election = self.get_by_id(election_id)
        if election:
            self.db.delete(election)
            self.db.commit()

    def start_election(self, election_id: int) -> Optional[Election]:
        return self.update(election_id, {"status": "active"})

    def end_election(self, election_id: int) -> Optional[Election]:
        return self.update(election_id, {"status": "completed"})


class SqlAlchemyCandidateRepository(ICandidateRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, candidate: Candidate) -> Candidate:
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def get_by_election_id(self, election_id: int) -> List[Candidate]:
        return self.db.query(Candidate).filter(Candidate.election_id == election_id).all()

    def get_by_id(self, candidate_id: int) -> Optional[Candidate]:
        return self.db.query(Candidate).filter(Candidate.id == candidate_id).first()

    def update(self, candidate_id: int, update_data: Dict[str, Any]) -> Optional[Candidate]:
        candidate = self.get_by_id(candidate_id)
        if candidate:
            for key, value in update_data.items():
                setattr(candidate, key, value)
            self.db.commit()
            self.db.refresh(candidate)
        return candidate

    def delete(self, candidate_id: int) -> None:
        candidate = self.get_by_id(candidate_id)
        if candidate:
            self.db.delete(candidate)
            self.db.commit()
