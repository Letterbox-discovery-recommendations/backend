from sqlmodel import Field, SQLModel, Relationship
from typing import TYPE_CHECKING

# Importa los modelos principales solo para el chequeo de tipos
if TYPE_CHECKING:
    from .real_person import RealPerson
    from .movie import Movie


class CastLink(SQLModel, table=True):
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)
    person_id: int | None = Field(
        default=None, foreign_key="realperson.id", primary_key=True
    )
    personaje: str
    orden: int

    movie: "Movie" = Relationship(back_populates="cast_links")
    person: "RealPerson" = Relationship(back_populates="cast_links")


class MovieGenreLink(SQLModel, table=True):
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)
    genre_id: int | None = Field(default=None, foreign_key="genre.id", primary_key=True)


class MoviePlatformLink(SQLModel, table=True):
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)
    platform_id: int | None = Field(
        default=None, foreign_key="platform.id", primary_key=True
    )