from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict

class IUserRepository(ABC):
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[Any]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        pass

    @abstractmethod
    def create(self, user_data: Any) -> Any:
        pass

    @abstractmethod
    def update_role(self, user_id: int, role: str) -> Optional[Any]:
        pass

    @abstractmethod
    def delete(self, user_id: int) -> None:
        pass

class IElectionRepository(ABC):
    @abstractmethod
    def create(self, election_data: Any) -> Any:
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        pass

    @abstractmethod
    def get_by_id(self, election_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def update(self, election_id: int, update_data: Dict[str, Any]) -> Optional[Any]:
        pass

    @abstractmethod
    def delete(self, election_id: int) -> None:
        pass

    @abstractmethod
    def start_election(self, election_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def end_election(self, election_id: int) -> Optional[Any]:
        pass

class ICandidateRepository(ABC):
    @abstractmethod
    def create(self, candidate_data: Any) -> Any:
        pass

    @abstractmethod
    def get_by_election_id(self, election_id: int) -> List[Any]:
        pass

    @abstractmethod
    def get_by_id(self, candidate_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def update(self, candidate_id: int, update_data: Dict[str, Any]) -> Optional[Any]:
        pass

    @abstractmethod
    def delete(self, candidate_id: int) -> None:
        pass

class IVotingTokenRepository(ABC):
    @abstractmethod
    def create_token(self, token_hash: str, user_id: int, election_id: int, expires_at: Any) -> Any:
        pass

    @abstractmethod
    def get_token(self, user_id: int, election_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def mark_as_used(self, token: Any) -> Any:
        pass

class IVoteRepository(ABC):
    @abstractmethod
    def create(self, vote_data: Any) -> Any:
        pass

    @abstractmethod
    def get_last_vote(self, election_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def get_results(self, election_id: int) -> List[Dict[str, Any]]:
        pass
