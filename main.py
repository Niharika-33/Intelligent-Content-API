from fastapi import FastAPI
from app.api.v1 import router as api_router

# Initialize the FastAPI application
app = FastAPI(
    title="The Intelligent Content API",
    description="Backend Engineering Intern Assignment.",
    version="1.0.0",
)

# Include the API router
# All API endpoints will be accessed via /api/v1/...
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Intelligent Content API. Check /docs for documentation."}