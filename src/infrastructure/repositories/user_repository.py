from typing import List, Optional
from sqlalchemy.orm import Session
from src.domain.interfaces import IUserRepository
from src.infrastructure.database.models import User

class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_role(self, user_id: int, role: str) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.role = role
            self.db.commit()
            self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> None:
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
