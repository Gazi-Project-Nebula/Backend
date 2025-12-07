# Handles all database setup and defines the structure of the tables (the schema).
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime
from config import settings

# The database engine connects to the database specified in the config.
engine = create_engine(settings.DATABASE_URL
                       #for SQLite use the line below instead
                       #, connect_args={"check_same_thread": False}
                       )

# A SessionLocal class is a factory for creating new database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is a class that all our database models will inherit from.
Base = declarative_base()

# Defines the 'users' table in the database.
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="voter")  # Roles can be 'admin' or 'voter'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    elections = relationship("Election", back_populates="creator")
    tokens = relationship("VotingToken", back_populates="user")

# Defines the 'elections' table.
class Election(Base):
    __tablename__ = "elections"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    status = Column(String, default="pending")
    created_by = Column(Integer, ForeignKey("users.id"))

    creator = relationship("User", back_populates="elections")
    candidates = relationship("Candidate", back_populates="election")
    votes = relationship("Vote", back_populates="election")
    tokens = relationship("VotingToken", back_populates="election")

# Defines the 'candidates' table for each election.
class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bio = Column(Text)
    election_id = Column(Integer, ForeignKey("elections.id"))

    election = relationship("Election", back_populates="candidates")
    votes = relationship("Vote", back_populates="candidate")

# Defines 'voting_tokens' to ensure one person, one vote.
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

# Defines the 'votes' table, representing anonymous ballots.
class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    vote_hash = Column(String, unique=True, index=True) # A receipt for the voter
    prev_vote_hash = Column(String) # For the tamper-evident chain
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    election_id = Column(Integer, ForeignKey("elections.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))

    election = relationship("Election", back_populates="votes")
    candidate = relationship("Candidate", back_populates="votes")

# A function to create all the tables defined above.
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

# If this file is run directly, it creates the database and tables.
if __name__ == "__main__":
    create_db_and_tables()
