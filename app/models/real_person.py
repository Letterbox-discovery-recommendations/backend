from typing import List, TYPE_CHECKING
from sqlmodel import Relationship, SQLModel, Field

if TYPE_CHECKING:
    from .links import CastLink


class RealPerson(SQLModel, table=True):
    """Representa a una persona del elenco (un actor) en la base de datos."""
    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    imagenUrl: str | None = None
    genero: int

    cast_links: List["CastLink"] = Relationship(back_populates="person")

