from typing import List, TYPE_CHECKING
from sqlmodel import Relationship, SQLModel, Field

from .movie import MovieActorLink

if TYPE_CHECKING:
    from .movie import Movie


class Actor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    age: int
    gender: str

    movies: List["Movie"] = Relationship(
        back_populates="cast", link_model=MovieActorLink
    )
