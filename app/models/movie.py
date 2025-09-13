from typing import List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from datetime import date


from .links import CastLink, MovieGenreLink, MoviePlatformLink

if TYPE_CHECKING:
    from .director import Director
    from .genre import Genre
    from .platform import Platform


class Movie(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(index=True)
    sinopsis: str
    duracionMinutos: int
    fechaEstreno: date | None = None
    posterUrl: str | None = None
    activa: bool = Field(default=True)

    director_id: int | None = Field(default=None, foreign_key="director.id")
    director: "Director" = Relationship(back_populates="movies_directed")

    cast_links: List["CastLink"] = Relationship(
        back_populates="movie", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    generos: List["Genre"] = Relationship(
        back_populates="movies", link_model=MovieGenreLink
    )

    plataformas: List["Platform"] = Relationship(
        back_populates="movies", link_model=MoviePlatformLink
    )
