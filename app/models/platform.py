from typing import List, TYPE_CHECKING
from sqlmodel import Relationship, SQLModel, Field

from .links import MoviePlatformLink

if TYPE_CHECKING:
    from .movie import Movie


class Platform(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    logoUrl: str | None = None

    movies: List["Movie"] = Relationship(
        back_populates="plataformas", link_model=MoviePlatformLink
    )
