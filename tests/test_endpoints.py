import pytest
import pytest_asyncio
import asyncio
import sys
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# CRITICAL FIX: Inject the project root path to resolve ModuleNotFoundError
sys.path.insert(0, os.path.abspath("."))

# Import core application components for testing
from main import app
from app.db.database import Base, get_db_session
from app.core.test_config import TEST_DATABASE_URL
from app.models.user import User  # Used for type hinting


# --- 1. Database Setup for Testing ---

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=test_engine,
    class_=AsyncSession,
)


async def override_get_db_session():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db_session] = override_get_db_session


# --- 2. Pytest Fixture for Test Client and Tables ---


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncClient:
    """
    Async fixture to provide the Async Test Client and manage table setup/teardown.
    """
    # Setup: create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Teardown: drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# --- 3. Test Cases ---


@pytest.mark.asyncio
async def test_1_create_and_login_user(client: AsyncClient):
    signup_data = {
        "email": "testuser@pytest.com",
        "password": "TestPassword123",
    }
    response = await client.post("/api/v1/signup", json=signup_data)

    assert response.status_code == 201
    assert response.json()["email"] == "testuser@pytest.com"

    login_data = {
        "username": "testuser@pytest.com",
        "password": "TestPassword123",
    }
    response = await client.post(
        "/api/v1/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_2_read_protected_content(client: AsyncClient):
    login_data = {
        "username": "testuser@pytest.com",
        "password": "TestPassword123",
    }
    login_response = await client.post(
        "/api/v1/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    read_response = await client.get("/api/v1/contents", headers=headers)

    assert read_response.status_code == 200
    assert isinstance(read_response.json(), list)

    unauth_response = await client.get("/api/v1/contents")
    assert unauth_response.status_code == 401
    assert unauth_response.json()["detail"] == "Not authenticated"
