from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime

# --- Input Schemas ---

class UserCreate(BaseModel):
    """Schema for user registration input."""
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    """Schema for user login input."""
    email: EmailStr
    password: str

# --- Output Schemas ---

class UserBase(BaseModel):
    """Base schema for user data."""
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime.datetime

    class Config:
        # Allows Pydantic to read data from the SQLAlchemy ORM model (key requirement for FastAPI)
        from_attributes = True 

class Token(BaseModel):
    """Schema for the returned JWT token."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for data inside the JWT token (payload)."""
    user_id: Optional[int] = None