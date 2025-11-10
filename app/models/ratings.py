from sqlmodel import Field, SQLModel
from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint


class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: int = Field(foreign_key="movie.id", nullable=False)
    user_id: int = Field(nullable=False)
    rating: float = Field(nullable=False)
    comment: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("movie_id", "user_id", name="unique_user_movie_review"),
    )