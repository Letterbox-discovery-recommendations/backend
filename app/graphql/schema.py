import strawberry
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from datetime import date

# Importa los nuevos modelos de la base de datos
from app.db.config import get_session
from app.models import (
    Movie as DBMovie,
    RealPerson as DBRealPerson,

    CastLink as DBCastLink,
)




@strawberry.type
class RealPersonType:
    """Representa a una persona (actor o director) en el sistema."""
    id: int
    nombre: str
    imagenUrl: Optional[str]
    genero: int


@strawberry.type
class PlatformType:
    """Representa una plataforma de streaming."""

    id: int
    nombre: str
    logoUrl: Optional[str]


@strawberry.type
class CastLinkType:
    """
    Representa la participación de un actor en una película,
    incluyendo el personaje que interpreta.
    """

    personaje: str
    orden: int

    @strawberry.field
    def actor(self) -> RealPersonType:
        """Resuelve la persona real que interpreta el papel."""
        return self.person  # type: ignore


# --- 2. Tipos Actualizados 🔄 ---


@strawberry.type
class GenreType:
    """Representa un género de película."""
    id: int
    nombre: str  # name -> nombre


@strawberry.type
class MovieType:
    """Representa una película con todos sus detalles."""

    id: int
    titulo: str
    sinopsis: str
    duracionMinutos: int
    fechaEstreno: Optional[date]
    posterUrl: Optional[str]

    # Relaciones actualizadas
    @strawberry.field
    def director(self) -> RealPersonType:
        """El director de la película."""
        return self.director  # type: ignore

    @strawberry.field
    def generos(self) -> List[GenreType]:
        """Los géneros de la película."""
        return self.generos  # type: ignore

    @strawberry.field
    def plataformas(self) -> List[PlatformType]:
        """Las plataformas donde la película está disponible."""
        return self.plataformas  # type: ignore

    @strawberry.field
    def elenco(self) -> List[CastLinkType]:
        """El elenco de la película, incluyendo el personaje y orden."""
        return self.cast_links  # type: ignore


# --- 3. Query Actualizada y Optimizada ⚙️ ---


@strawberry.type
class Query:
    @strawberry.field
    def peliculas(self, titulo: Optional[str] = None) -> List[MovieType]:
        """Obtiene una lista de películas, opcionalmente filtrada por título."""
        db_session: Session = next(get_session())

        # El statement ahora carga todas las relaciones necesarias de una sola vez
        # para evitar múltiples consultas a la base de datos (problema N+1)
        statement = select(DBMovie).options(
            selectinload(DBMovie.director),
            selectinload(DBMovie.generos),
            selectinload(DBMovie.plataformas),
            # Carga anidada: carga los enlaces del elenco Y la persona en cada enlace
            selectinload(DBMovie.cast_links).selectinload(DBCastLink.person),
        )

        if titulo:
            statement = statement.where(
                DBMovie.titulo.icontains(titulo)
            )

        results = db_session.exec(statement).unique().all()
        db_session.close()
        return results  # type: ignore

    @strawberry.field
    def plataformas(self) -> List[PlatformType]:
        return self.plataformas # type: ignore

    @strawberry.field
    def personas(self, nombre: Optional[str] = None) -> List[RealPersonType]:
        """Obtiene una lista de personas (actores/directores)."""
        db_session: Session = next(get_session())

        statement = select(DBRealPerson)
        if nombre:
            statement = statement.where(DBRealPerson.nombre.icontains(nombre))

        results = db_session.exec(statement).all()
        db_session.close()
        return results  # type: ignore

    @strawberry.field
    def pelicula(self, id: int) -> Optional[MovieType]:
        """Obtiene una película por su ID."""
        db_session: Session = next(get_session())

        statement = (
            select(DBMovie)
            .options(
                selectinload(DBMovie.director),
                selectinload(DBMovie.generos),
                selectinload(DBMovie.plataformas),
                selectinload(DBMovie.cast_links).selectinload(DBCastLink.person),
            )
            .where(DBMovie.id == id)
        )

        result = db_session.exec(statement).first()
        db_session.close()
        return result # type: ignore

schema = strawberry.Schema(query=Query)