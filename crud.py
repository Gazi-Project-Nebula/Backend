# Contains reusable functions to interact with the database (Create, Read, Update, Delete).
from sqlalchemy.orm import Session
import database, schemas
from passlib.context import CryptContext

# Sets up the password hashing scheme.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Finds a user in the database by their username.
def get_user_by_username(db: Session, username: str):
    return db.query(database.User).filter(database.User.username == username).first()

# Creates a new user in the database with a hashed password.
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = database.User(username=user.username, password_hash=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
