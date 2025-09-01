from typing import List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .actor import Actor
    from .genre import Genre


class MovieActorLink(SQLModel, table=True):
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)
    actor_id: int | None = Field(default=None, foreign_key="actor.id", primary_key=True)


class MovieGenreLink(SQLModel, table=True):
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)
    genre_id: int | None = Field(default=None, foreign_key="genre.id", primary_key=True)


class Movie(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    description: str
    release_year: int
    director: str
    duration: int
    platform: str
    rating: float = Field(default=0.0, ge=0, le=5)




    cast: List["Actor"] = Relationship(
        back_populates="movies", link_model=MovieActorLink
    )
    genres: List["Genre"] = Relationship(
        back_populates="movies", link_model=MovieGenreLink
    )
