from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime

# --- Input Schemas (Used for POST /signup and POST /login body) ---

class UserCreate(BaseModel):
    """Schema for user registration and login input (email/password)."""
    email: EmailStr
    password: str

# NOTE: We reuse UserCreate for UserLogin input, as they are identical fields.

# --- Output Schemas (Used for API responses) ---

class UserPublic(BaseModel):
    """
    Schema for public user data returned by the API (e.g., after signup).
    CRITICAL: Excludes sensitive fields like 'hashed_password'.
    """
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True 

class Token(BaseModel):
    """Schema for the returned JWT token."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for data inside the JWT token (payload)."""
    user_id: Optional[int] = None