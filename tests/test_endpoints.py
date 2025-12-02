import sys
import os
# CRITICAL FIX: Inject the project root directory into sys.path for Pytest to find 'main.py'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import core application components for testing
from main import app # <-- CHANGED: Import app directly from main.py
from app.db.database import Base, get_db_session
from app.core.test_config import TEST_DATABASE_URL # Import the test URL
from app.models.user import User # Used for type hinting
from app.models.content import Content, Sentiment # Ensure Content models are imported

# --- 1. Database Setup for Testing ---

# Create asynchronous engine for SQLite in-memory database
test_engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=False, 
    connect_args={"check_same_thread": False} # Required for SQLite/FastAPI async testing
)

# Define the session local factory
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=test_engine,
    class_=AsyncSession # Use AsyncSession for testing
)

# Function to override the database dependency in FastAPI
# This ensures that our endpoints use the SQLite database during tests
async def override_get_db_session():
    async with TestingSessionLocal() as session:
        yield session

# Apply the dependency override
app.dependency_overrides[get_db_session] = override_get_db_session

# --- 2. Pytest Fixture for Test Client and Tables ---

@pytest.fixture(scope="module", autouse=True)
def event_loop():
    """Fixture to provide a module-scoped event loop."""
    loop = asyncio.get_event_loop()
    yield loop

@pytest.fixture(scope="module")
async def client():
    """Fixture to provide the Async Test Client and manage table setup/teardown."""
    # Setup: Create tables before tests run
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Yield the test client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
        
    # Teardown: Drop tables after tests finish
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- 3. Test Cases (2 Required for Bonus Points) ---

@pytest.mark.asyncio
async def test_1_create_and_login_user(client: AsyncClient):
    """
    Tests POST /api/v1/signup and POST /api/v1/login.
    Verifies user creation, password hashing, and successful JWT generation.
    """
    # 1. Test Signup
    signup_data = {
        "email": "testuser@pytest.com", 
        "password": "TestPassword123"
    }
    response = await client.post("/api/v1/signup", json=signup_data)
    
    assert response.status_code == 201
    assert response.json()["email"] == "testuser@pytest.com"

    # 2. Test Login (Requires Form Data input structure)
    login_data = {
        "username": "testuser@pytest.com",  # OAuth2 uses 'username' field for email
        "password": "TestPassword123"
    }
    # Note the header: must be 'application/x-www-form-urlencoded' for OAuth2PasswordRequestForm
    response = await client.post(
        "/api/v1/login", 
        data=login_data, 
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_2_read_protected_content(client: AsyncClient):
    """
    Tests GET /api/v1/contents (Protected Route).
    Verifies token authentication works and returns content (or an empty list).
    """
    # 1. Log in to get a valid token
    login_data = {
        "username": "testuser@pytest.com", 
        "password": "TestPassword123"
    }
    login_response = await client.post(
        "/api/v1/login", 
        data=login_data, 
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_response.json()["access_token"]
    
    # 2. Test reading content with the valid token
    headers = {"Authorization": f"Bearer {token}"}
    read_response = await client.get("/api/v1/contents", headers=headers)
    
    # Should succeed (returns 200 OK, even if content list is empty)
    assert read_response.status_code == 200
    assert isinstance(read_response.json(), list)

    # 3. Test Unauthorized Access (without token)
    unauth_response = await client.get("/api/v1/contents")
    assert unauth_response.status_code == 401
    assert unauth_response.json()["detail"] == "Not authenticated"