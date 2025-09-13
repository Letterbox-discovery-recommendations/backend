from typing import List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from .movie import MovieGenreLink

if TYPE_CHECKING:
    from .movie import Movie


class Genre(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = Field(default=None)

    movies: List["Movie"] = Relationship(
        back_populates="genres", link_model=MovieGenreLink
    )
