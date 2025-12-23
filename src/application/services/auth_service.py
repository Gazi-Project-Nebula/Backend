from typing import Optional
from src.domain.interfaces import IUserRepository
from src.infrastructure.security.utils import verify_password, get_password_hash, create_access_token
from src.infrastructure.database.models import User
from src.application import schemas
from src.core.config import settings
from datetime import timedelta

class AuthService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def register_user(self, user_create: schemas.UserCreate) -> User:
        if self.user_repo.get_by_username(user_create.username):
            raise ValueError("Username already registered")
        
        hashed_password = get_password_hash(user_create.password)
        # Force default role to voter if not specified, though schema defaults it.
        # Logic from main.py: user.role = "voter"
        role = "voter" 
        
        new_user = User(
            username=user_create.username,
            password_hash=hashed_password,
            role=role
        )
        return self.user_repo.create(new_user)

    def authenticate_user(self, username, password) -> Optional[User]:
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def create_user_token(self, user: User):
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return access_token

    def get_users(self, skip: int = 0, limit: int = 100):
        return self.user_repo.get_all(skip, limit)

    def update_user_role(self, user_id: int, role: str):
        return self.user_repo.update_role(user_id, role)

    def delete_user(self, user_id: int):
        return self.user_repo.delete(user_id)
