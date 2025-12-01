from fastapi import APIRouter

router = APIRouter()

# Placeholder for Auth (/signup, /login) and Content (/contents) endpoints
# These will be fleshed out in the next step.

@router.get("/status")
async def get_status():
    return {"status": "OK", "message": "API is running"}