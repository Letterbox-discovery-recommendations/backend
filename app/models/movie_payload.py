from pydantic import BaseModel
from datetime import date


class RealPerson(BaseModel):
    id: int
    nombre: str
    imagen: str | None


class Actor(BaseModel):
    id: int
    actor: RealPerson


class Genre(BaseModel):
    id: int
    nombre: str


class Cast(BaseModel):
    id: int
    personaje: str
    orden: int | None = None
    personaId: int
    nombrePersona: str
    imagenPersona: str | None


class Platform(BaseModel):
    id: int
    nombre: str
    logoUrl: str | None


class Movie(BaseModel):
    id: int
    titulo: str
    sinopsis: str
    duracionMinutos: int
    fechaEstreno: date | None
    poster: str | None
    activa: bool
    director: RealPerson | None
    elenco: list[Cast]
    generos: list[Genre]
    plataformas: list[Platform]