from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.schemas.user import UserCreate, Token
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.core.config import settings
from sqlalchemy import select # Required for async querying

router = APIRouter()

# --- 1. /signup Endpoint ---
@router.post("/signup", response_model=UserCreate, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    # Check if user already exists
    user_exists = await db.scalar(
        select(User).where(User.email == user_data.email)
    )
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # Hash the password
    hashed_password = get_password_hash(user_data.password)

    # Create new user model instance
    new_user = User(
        email=user_data.email, 
        hashed_password=hashed_password
    )

    # Add to database and commit
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Return user details (without password)
    return new_user

# --- 2. /login Endpoint ---
@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: UserCreate, # Using UserCreate schema for email/password input
    db: AsyncSession = Depends(get_db_session)
):
    # Retrieve user by email
    user = await db.scalar(
        select(User).where(User.email == form_data.email)
    )

    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the JWT access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, # 'sub' stands for subject, we use user ID here
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Placeholder for the old status check
@router.get("/status")
async def get_status():
    return {"status": "OK", "message": "API is running"}