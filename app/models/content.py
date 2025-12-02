from __future__ import annotations

import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    func,
    Text,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    # Only imported for type hints; avoids circular import at runtime
    from app.models.user import User


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

    owner: Mapped["User"] = relationship(back_populates="contents")

    def __repr__(self) -> str:
        return f"Content(id={self.id!r}, owner_id={self.owner_id!r}, summary={self.summary[:20]!r})"