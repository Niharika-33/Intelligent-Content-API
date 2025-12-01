from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from typing import AsyncGenerator

# 1. Base Class for Models
class Base(AsyncAttrs, DeclarativeBase):
    pass

# 2. Database Engine Setup
# create_async_engine uses the URL from settings (e.g., mysql+aiomysql://...)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True  # Set to False in production
)

# 3. Asynchronous Session Maker
# This factory creates new session objects bound to the engine
AsyncSessionLocal = async_sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False  # Important for async
)

# 4. Dependency for FastAPI Endpoints
# This function yields a new database session for each request
async def get_db_session() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        yield session

# 5. Function to Create Tables (Used in main.py)
async def create_db_and_tables():
    async with engine.begin() as conn:
        # Import Base and then create all tables defined from it
        # NOTE: Importing User and Content here ensures tables are registered
        from app.models.user import User
        from app.models.content import Content
        await conn.run_sync(Base.metadata.create_all)