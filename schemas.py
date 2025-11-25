# Defines the data shapes (schemas) that are used for API requests and responses
# It helps with data validation and documentation
from pydantic import BaseModel
from typing import Optional

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
    password: str
    role: str = "voter"

# Schema for returning user information in API responses (omits password)
class User(UserBase):
    id: int
    role: str

    class Config:
        # Allows the model to be created from database objects
        from_attributes = True
