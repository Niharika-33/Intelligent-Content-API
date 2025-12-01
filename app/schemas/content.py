from pydantic import BaseModel, Field
from typing import Optional
from app.models.content import Sentiment # Import the Enum from the models file
import datetime

# --- Input Schemas ---

class ContentCreate(BaseModel):
    """Schema for input when a user uploads content."""
    raw_content: str = Field(..., description="The main text body to be summarized and analyzed.")

# --- Output Schemas ---

class ContentBase(BaseModel):
    """Base schema for content data."""
    id: int
    raw_content: str
    owner_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ContentAnalysisResults(ContentBase):
    """Schema for content including the LLM analysis results."""
    # Note: These fields are optional because they are NULL initially, before the LLM processes them.
    summary: Optional[str] = None
    sentiment: Optional[Sentiment] = None