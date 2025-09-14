import strawberry
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy import func  # noqa: F401
from sqlalchemy.orm import selectinload
from datetime import date

# Importa los nuevos modelos de la base de datos
from app.db.config import get_session
from app.models import (
    Movie as DBMovie,
    RealPerson as DBRealPerson,
    Platform as DBPlatform,  # noqa: F401
    CastLink as DBCastLink,
    Genre as DBGenre,
    Review as DBReview,  
    MovieGenreLink,
    MoviePlatformLink,
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
    def director(self) -> Optional[RealPersonType]:
        """El director de la película."""
        return self.director  # type: ignore
    
    @strawberry.field
    def ratingPelicula(self) -> Optional[float]:
        """El rating promedio de la película basado en reseñas."""
        db_session: Session = next(get_session())
        avg_rating = db_session.exec(
            select(func.avg(DBReview.rating)).where(DBReview.movie_id == self.id)
        ).first()
        db_session.close()
        return avg_rating if avg_rating is not None else None  # Devuelve None si no hay reseñas

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


@strawberry.type
class Query:
    @strawberry.field
    def peliculas(
        self,
        titulo: Optional[str] = None,
        generos: Optional[List[str]] = None,
        plataformas: Optional[List[str]] = None,
        sort : Optional[str] = None,
        minDuration: Optional[int] = 0,
        maxDuration: Optional[int] = 0,
        minYear: Optional[int] = 0,
        maxYear: Optional[int] = 0,
    ) -> List[MovieType]:
        """Obtiene una lista de películas, opcionalmente filtrada por título."""
        db_session: Session = next(get_session())

        # El statement ahora carga todas las relaciones necesarias de una sola vez
        # para evitar múltiples consultas a la base de datos (problema N+1)
        statement = select(DBMovie).options(
            selectinload(DBMovie.director),
            selectinload(DBMovie.generos),
            selectinload(DBMovie.plataformas),
            selectinload(DBMovie.cast_links).selectinload(DBCastLink.person),
        )

        if titulo:
            statement = statement.where(func.lower(DBMovie.titulo).contains(titulo.lower()))

        if generos:
            generos_lower = [g.lower() for g in generos]
            statement = statement.where(
                DBMovie.generos.any(func.lower(DBGenre.nombre).in_(generos_lower))
            )
        if plataformas:
            plataformas_lower = [p.lower() for p in plataformas]
            statement = statement.where(
                DBMovie.plataformas.any(func.lower(DBPlatform.nombre).in_(plataformas_lower))
            )
        if minDuration:
            statement = statement.where(DBMovie.duracionMinutos >= minDuration)
        if maxDuration:
            statement = statement.where(DBMovie.duracionMinutos <= maxDuration)
        if minYear:
            statement = statement.where(func.extract('year', DBMovie.fechaEstreno) >= minYear)
        if maxYear:
            statement = statement.where(func.extract('year', DBMovie.fechaEstreno) <= maxYear)
        allowed_sorts = ["titulo", "titulo_desc", "duracionMinutos", "duracionMinutos_desc", "fechaEstreno", "fechaEstreno_desc"]
        if sort and sort not in allowed_sorts:
            sort = "titulo"  # Valor por defecto

        if sort == "titulo":
            statement = statement.order_by(DBMovie.titulo.asc())
        elif sort == "titulo_desc":
            statement = statement.order_by(DBMovie.titulo.desc())
        elif sort == "duracionMinutos":
            statement = statement.order_by(DBMovie.duracionMinutos.asc())
        elif sort == "duracionMinutos_desc":
            statement = statement.order_by(DBMovie.duracionMinutos.desc())
        elif sort == "fechaEstreno":
            statement = statement.order_by(DBMovie.fechaEstreno.asc())
        elif sort == "fechaEstreno_desc":
            statement = statement.order_by(DBMovie.fechaEstreno.desc())
        else:
            statement = statement.order_by(DBMovie.id.asc())  # Por defecto

        results = db_session.exec(statement).unique().all()
        db_session.close()
        return results  # type: ignore

    @strawberry.field
    def plataformas(self) -> List[PlatformType]:
        db_session: Session = next(get_session())
        statement = select(DBPlatform)
        results = db_session.exec(statement).all()
        db_session.close()
        return results  # type: ignore

    @strawberry.field
    def generos(self) -> List[GenreType]:
        db_session: Session = next(get_session())
        statement = select(DBGenre)
        results = db_session.exec(statement).all()
        db_session.close()
        return results

    @strawberry.field
    def personas(self, nombre: Optional[str] = None) -> List[RealPersonType]:
        """Obtiene una lista de personas (actores/directores)."""
        db_session: Session = next(get_session())

        statement = select(DBRealPerson)
        if nombre:
            statement = statement.where(DBRealPerson.nombre.contains(nombre.lower()))

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
        return result  # type: ignore


schema = strawberry.Schema(query=Query)
