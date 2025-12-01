from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from app.core.config import settings

# --- Password Hashing Setup ---

# Define the context for password hashing (using bcrypt)
# Added 'bcrypt' to schemes explicitly, passlib should handle the backend better.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a password for storage. Handles the 72 byte limit internally."""
    
    # We truncate the password to fit the bcrypt limit (72 bytes) before hashing.
    # This ensures the API doesn't crash on long, valid input.
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
        
    return pwd_context.hash(password)

# --- JWT Token Management ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Use the default expiration time from settings if not provided
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Encode the token using the secret key and algorithm
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt