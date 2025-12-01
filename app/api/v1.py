from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.schemas.user import UserCreate, Token, UserPublic
from app.core.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.core.config import settings
from sqlalchemy.future import select as sql_select
from typing import List

# --- Protected Imports ---
# NOTE: We keep OAuth2PasswordBearer here only for the dependency structure (get_current_user)
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

# --- Model Imports ---
from app.models.user import User
from app.models.content import Content, Sentiment
from app.schemas.content import ContentCreate, ContentAnalysisResults
from app.services.llm_service import analyze_content 
# -------------------------------------------------------------------------

router = APIRouter()
# Set the correct token URL for the Authorize modal
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login") 

# --- AUTHENTICATION DEPENDENCY ---
async def get_current_user(
    db: AsyncSession = Depends(get_db_session), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency that authenticates the user based on the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception

    user = await db.scalar(
        sql_select(User).where(User.id == int(user_id))
    )
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
        
    return user
    
# --- 1. /signup Endpoint (Unprotected) ---
@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    # Check if user already exists
    user_exists = await db.scalar(
        sql_select(User).where(User.email == user_data.email)
    )
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # Hash the password (using safe SHA256)
    hashed_password = get_password_hash(user_data.password)

    # Create new user model instance
    new_user = User(
        email=user_data.email, 
        hashed_password=hashed_password
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

# --- 2. /login Endpoint (FINAL FIX FOR SWAGGER UI) ---
# We switch this back to using UserCreate (JSON body) because Swagger only offers JSON.
@router.post("/login", response_model=Token)
async def login_for_access_token(
    user_data: UserCreate, # Expect JSON input like POST /signup
    db: AsyncSession = Depends(get_db_session)
):
    # Retrieve user by email
    user = await db.scalar(
        sql_select(User).where(User.email == user_data.email)
    )

    # Check if user exists and password is correct
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the JWT access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires
    )
    
    # The login succeeded using JSON input, which is accepted by Swagger UI.
    return {"access_token": access_token, "token_type": "bearer"}

# --- 3. POST /contents Endpoint (Create & AI Process) ---
@router.post("/contents", response_model=ContentAnalysisResults, status_code=status.HTTP_202_ACCEPTED)
async def create_content(
    content_data: ContentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user) # Protected endpoint
):
    """
    Uploads content, saves it to the database, and triggers asynchronous AI processing.
    """
    
    new_content = Content(
        raw_content=content_data.raw_content,
        owner_id=current_user.id,
    )
    db.add(new_content)
    await db.commit()
    await db.refresh(new_content)

    summary, sentiment = await analyze_content(new_content.raw_content)

    if summary is not None or sentiment is not None:
        new_content.summary = summary
        new_content.sentiment = sentiment.value if sentiment else None 
        
        await db.commit()
        await db.refresh(new_content)

    return new_content

# --- 4. GET /contents Endpoint (Retrieve All) ---
@router.get("/contents", response_model=List[ContentAnalysisResults])
async def read_contents(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user) # Protected endpoint
):
    """
    Retrieves all content submitted by the authenticated user.
    """
    result = await db.execute(
        sql_select(Content)
        .where(Content.owner_id == current_user.id)
    )
    contents = result.scalars().all()
    return contents

# --- 5. GET /contents/{id} Endpoint (Retrieve Specific) ---
@router.get("/contents/{content_id}", response_model=ContentAnalysisResults)
async def read_content_by_id(
    content_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user) # Protected endpoint
):
    """
    Retrieves a specific piece of content by ID, ensuring ownership.
    """
    content = await db.scalar(
        sql_select(Content)
        .where(Content.id == content_id)
        .where(Content.owner_id == current_user.id)
    )
    
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Content not found or you do not own this content"
        )
    return content

# --- 6. DELETE /contents/{id} Endpoint ---
@router.delete("/contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user) # Protected endpoint
):
    """
    Deletes a specific piece of content by ID, ensuring ownership.
    """
    content_to_delete = await db.scalar(
        sql_select(Content)
        .where(Content.id == content_id)
        .where(Content.owner_id == current_user.id)
    )
    
    if content_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Content not found or you do not own this content"
        )

    await db.delete(content_to_delete)
    await db.commit()
    return

# Placeholder for the old status check
@router.get("/status")
async def get_status():
    return {"status": "OK", "message": "API is running"}