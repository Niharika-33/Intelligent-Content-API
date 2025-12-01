from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, func, Boolean
from app.db.database import Base
import datetime
from typing import List

# Import Content model here? NO! Use a string reference instead to break the circle.
# from app.models.content import Content 

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())

    # CRITICAL FIX: Use the string name 'Content' instead of importing the model object
    contents: Mapped[List["Content"]] = relationship(back_populates="owner")
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"
        