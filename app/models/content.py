from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, func, Text, ForeignKey, Enum
from app.db.database import Base
import datetime
import enum

# Import User model here? NO! Use a string reference instead to break the circle.
# from app.models.user import User 

# Define the sentiment choices as an Enum
class Sentiment(enum.Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"
    
class Content(Base):
    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    raw_content: Mapped[str] = mapped_column(Text)
    
    # LLM Generated Fields
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    sentiment: Mapped[Sentiment] = mapped_column(Enum(Sentiment), nullable=True) 
    
    # Metadata
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())

    # Relationship to User (Foreign Key)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # CRITICAL FIX: Use the string name 'User' instead of importing the model object
    owner: Mapped["User"] = relationship(back_populates="contents")
    
    def __repr__(self) -> str:
        return f"Content(id={self.id!r}, owner_id={self.owner_id!r}, summary={self.summary[:20]!r})"