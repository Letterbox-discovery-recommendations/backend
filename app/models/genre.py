from typing import List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from .links import MovieGenreLink

if TYPE_CHECKING:
    from .movie import Movie


class Genre(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str

    movies: List["Movie"] = Relationship(
        back_populates="generos", link_model=MovieGenreLink
    )
