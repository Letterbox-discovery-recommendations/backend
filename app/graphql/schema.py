import strawberry
from typing import List, Optional
from datetime import date

# NUEVO: Importaciones de Async
from sqlmodel.ext.asyncio.session import AsyncSession
from strawberry.types import Info
from sqlmodel import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload

# Importa los nuevos modelos de la base de datos
# from app.db.utils import get_session  # <-- Ya no es necesario aquí
from app.models import (
    Movie as DBMovie,
    RealPerson as DBRealPerson,
    Platform as DBPlatform,
    CastLink as DBCastLink,
    Genre as DBGenre,
    Review as DBReview,
)

# --- (Los Tipos: RealPersonType, PlatformType, CastLinkType, GenreType no cambian) ---


@strawberry.type
class RealPersonType:
    id: int
    nombre: str
    imagenUrl: Optional[str]
    genero: int


@strawberry.type
class PlatformType:
    id: int
    nombre: str
    logoUrl: Optional[str]


@strawberry.type
class CastLinkType:
    personaje: str
    orden: int

    @strawberry.field
    def actor(self) -> RealPersonType:
        return self.person  # type: ignore


@strawberry.type
class GenreType:
    id: int
    nombre: str


# --- (MovieType ya estaba casi listo, no necesita cambios) ---
@strawberry.type
class MovieType:
    """Representa una película con todos sus detalles."""

    id: int
    titulo: str
    sinopsis: str
    duracionMinutos: int
    fechaEstreno: Optional[date]
    posterUrl: Optional[str]

    @strawberry.field
    def director(self) -> Optional[RealPersonType]:
        return self.director  # type: ignore

    # Este ya estaba correcto
    @strawberry.field
    async def ratingPelicula(self, info: Info) -> Optional[float]:
        """El rating promedio de la película (cargado eficientemente)."""
        loader = info.context["rating_loader"]
        return await loader.load(self.id)

    @strawberry.field
    def generos(self) -> List[GenreType]:
        return self.generos  # type: ignore

    @strawberry.field
    def plataformas(self) -> List[PlatformType]:
        return self.plataformas  # type: ignore

    @strawberry.field
    def elenco(self) -> List[CastLinkType]:
        return self.cast_links  # type: ignore


# --- (Query: Aquí están todas las correcciones) ---
@strawberry.type
class Query:
    @strawberry.field
    async def peliculas(  # NUEVO: async def
        self,
        info: Info,  # NUEVO: info: Info
        titulo: Optional[str] = None,
        generos: Optional[List[str]] = None,
        plataformas: Optional[List[str]] = None,
        sort: Optional[str] = None,
        minDuration: Optional[int] = 0,
        maxDuration: Optional[int] = 0,
        minYear: Optional[int] = 0,
        maxYear: Optional[int] = 0,
    ) -> List[MovieType]:
        """Obtiene una lista de películas, opcionalmente filtrada por título."""

        # NUEVO: Obtener la sesión del contexto
        db: AsyncSession = info.context["db"]

        statement = select(DBMovie).options(
            selectinload(DBMovie.director),
            selectinload(DBMovie.generos),
            selectinload(DBMovie.plataformas),
            selectinload(DBMovie.cast_links).selectinload(DBCastLink.person),
        )

        # ... (Toda tu lógica de filtros y ordenamiento permanece igual) ...
        if titulo:
            statement = statement.where(
                func.lower(DBMovie.titulo).contains(titulo.lower())
            )
        if generos:
            generos_lower = [g.lower() for g in generos]
            statement = statement.where(
                DBMovie.generos.any(func.lower(DBGenre.nombre).in_(generos_lower))
            )
        if plataformas:
            plataformas_lower = [p.lower() for p in plataformas]
            statement = statement.where(
                DBMovie.plataformas.any(
                    func.lower(DBPlatform.nombre).in_(plataformas_lower)
                )
            )
        if minDuration:
            statement = statement.where(DBMovie.duracionMinutos >= minDuration)
        if maxDuration:
            statement = statement.where(DBMovie.duracionMinutos <= maxDuration)
        if minYear:
            statement = statement.where(
                func.extract("year", DBMovie.fechaEstreno) >= minYear
            )
        if maxYear:
            statement = statement.where(
                func.extract("year", DBMovie.fechaEstreno) <= maxYear
            )

        allowed_sorts = [
            "titulo",
            "titulo_desc",
            "duracionMinutos",
            "duracionMinutos_desc",
            "fechaEstreno",
            "fechaEstreno_desc",
        ]
        if sort and sort not in allowed_sorts:
            sort = "titulo"

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
            statement = statement.order_by(DBMovie.id.asc())

        # NUEVO: Usar 'await' para la ejecución
        results = await db.exec(statement)
        # NUEVO: Ya no se usa db_session.close()
        return results.unique().all()  # type: ignore

    @strawberry.field
    async def plataformas(
        self, info: Info
    ) -> List[PlatformType]:  # NUEVO: async + info
        db: AsyncSession = info.context["db"]  # NUEVO: context
        statement = select(DBPlatform)
        results = await db.exec(statement)  # NUEVO: await
        return results.all()  # type: ignore

    @strawberry.field
    async def generos(self, info: Info) -> List[GenreType]:  # NUEVO: async + info
        db: AsyncSession = info.context["db"]  # NUEVO: context
        statement = select(DBGenre)
        results = await db.exec(statement)  # NUEVO: await
        return results.all()

    @strawberry.field
    async def personas(
        self, info: Info, nombre: Optional[str] = None
    ) -> List[RealPersonType]:  # NUEVO: async + info
        """Obtiene una lista de personas (actores/directores)."""
        db: AsyncSession = info.context["db"]  # NUEVO: context

        statement = select(DBRealPerson)
        if nombre:
            # Asumiendo que DBRealPerson.nombre es case-insensitive o usas lower
            statement = statement.where(
                func.lower(DBRealPerson.nombre).contains(nombre.lower())
            )

        results = await db.exec(statement)  # NUEVO: await
        return results.all()  # type: ignore

    @strawberry.field
    async def pelicula(
        self, info: Info, id: int
    ) -> Optional[MovieType]:  # NUEVO: async + info
        """Obtiene una película por su ID."""
        db: AsyncSession = info.context["db"]  # NUEVO: context

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

        result = await db.exec(statement) # NUEVO: await
        return result.first()  # type: ignore


schema = strawberry.Schema(query=Query)