from typing import List, TYPE_CHECKING
from sqlmodel import Relationship, SQLModel, Field

if TYPE_CHECKING:
    from .movie import Movie


class Director(SQLModel, table=True):
    """Representa a un director de cine en la base de datos."""
    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    imagenUrl: str | None = None
    genero: int

    movies_directed: List["Movie"] = Relationship(back_populates="director")