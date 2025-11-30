# Defines the data shapes (schemas) that are used for API requests and responses
# It helps with data validation and documentation
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# Schema for the access token response
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for the data embedded within a JWT token
class TokenData(BaseModel):
    username: Optional[str] = None

# Base schema for a user, with common properties
class UserBase(BaseModel):
    username: str

# Schema used when creating a new user. Inherits from UserBase
class UserCreate(UserBase):
    # Limit password to 64 characters to stay safely under the 72-byte bcrypt limit
    password: str = Field(..., min_length=6, max_length=64)
    role: str = "voter"

# Schema for returning user information in API responses (omits password)
class User(UserBase):
    id: int
    role: str

    model_config = ConfigDict(from_attributes=True)

# --- ELECTION & CANDIDATE SCHEMAS ---

class CandidateBase(BaseModel):
    name: str
    description: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class Candidate(CandidateBase):
    id: int
    election_id: int
    
    model_config = ConfigDict(from_attributes=True)

class ElectionBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime

class ElectionCreate(ElectionBase):
    # The user sends a list of candidates when creating an election
    candidates: List[CandidateCreate]

class Election(ElectionBase):
    id: int
    is_active: bool
    created_by: int
    candidates: List[Candidate] = []

    model_config = ConfigDict(from_attributes=True)

# --- VOTING SCHEMAS ---

class VoteCreate(BaseModel):
    election_id: int
    candidate_id: int
    token: str

class VoteReceipt(BaseModel):
    vote_hash: str
    timestamp: datetime