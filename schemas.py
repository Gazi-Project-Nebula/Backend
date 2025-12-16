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

# Schema for Login request body
class UserLogin(BaseModel):
    username: str
    password: str

# Schema for returning user information in API responses (omits password)
class User(UserBase):
    id: int
    role: str

    model_config = ConfigDict(from_attributes=True)

# --- ELECTION & CANDIDATE SCHEMAS ---

class CandidateBase(BaseModel):
    name: str
    bio: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None

class Candidate(CandidateBase):
    id: int
    election_id: int
    
    model_config = ConfigDict(from_attributes=True)

class ElectionBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ElectionCreate(ElectionBase):
    # The user sends a list of candidates when creating an election
    candidates: List[CandidateCreate]

# NEW: Schema for the specific API request (POST /api/elections)
class ElectionCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    end_time: Optional[datetime] = None
    candidate_names: List[str]
    creator_id: Optional[int] = None

class Election(ElectionBase):
    id: int
    status: str
    created_by: int
    candidates: List[Candidate] = []

    model_config = ConfigDict(from_attributes=True)

class ElectionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

# --- VOTING SCHEMAS ---

class VoteCreate(BaseModel):
    election_id: int
    candidate_id: int
    token: str

class VoteCastRequest(BaseModel):
    election_id: int
    candidate_id: int
    user_id: int

class VoteReceipt(BaseModel):
    vote_hash: str
    timestamp: datetime


# --- RESULT SCHEMAS ---

class CandidateResult(BaseModel):
    id: int
    name: str
    vote_count: int

class ElectionResult(BaseModel):
    id: int
    title: str
    status: str
    results: List[CandidateResult]