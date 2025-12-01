from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1 import router as api_router
from app.db.database import create_db_and_tables 

# This is CRITICAL: Import the models module *here* so SQLAlchemy knows they exist
# before create_db_and_tables runs.
import app.models 

# 1. Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    print("Initializing database and creating tables...")
    await create_db_and_tables()
    print("Database initialization complete.")
    yield
    # Shutdown: (No specific action needed for this project)


# 2. Initialize the FastAPI application with the lifespan
app = FastAPI(
    title="The Intelligent Content API",
    description="Backend Engineering Intern Assignment.",
    version="1.0.0",
    lifespan=lifespan
)

# Include the API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Intelligent Content API. Check /docs for documentation."}