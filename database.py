from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
from .config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="voter")  # 'admin' or 'voter'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    elections = relationship("Election", back_populates="creator")
    tokens = relationship("VotingToken", back_populates="user")

class Election(Base):
    __tablename__ = "elections"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))

    creator = relationship("User", back_populates="elections")
    candidates = relationship("Candidate", back_populates="election")
    votes = relationship("Vote", back_populates="election")
    tokens = relationship("VotingToken", back_populates="election")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    election_id = Column(Integer, ForeignKey("elections.id"))

    election = relationship("Election", back_populates="candidates")
    votes = relationship("Vote", back_populates="candidate")

class VotingToken(Base):
    __tablename__ = "voting_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String, unique=True, index=True)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    election_id = Column(Integer, ForeignKey("elections.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    election = relationship("Election", back_populates="tokens")
    user = relationship("User", back_populates="tokens")

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    vote_hash = Column(String, unique=True, index=True)
    prev_vote_hash = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    election_id = Column(Integer, ForeignKey("elections.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))

    election = relationship("Election", back_populates="votes")
    candidate = relationship("Candidate", back_populates="votes")

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_db_and_tables()
