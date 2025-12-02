from __future__ import annotations

import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    # Only imported for type hints; avoids circular import at runtime
    from app.models.content import Content


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())

    # Relationship to Content (one-to-many)
    contents: Mapped[List["Content"]] = relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"
