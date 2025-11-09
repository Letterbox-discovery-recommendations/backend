import asyncio
import logging
from sqlmodel.ext.asyncio.session import AsyncSession  # NUEVO: AsyncSession
from app.models import (
    Movie as DBMovie,
    RealPerson,
    Genre,
    Platform,
    CastLink,
    PydanticMovie,
    Director,
)

# NUEVO: Importa la versión async del helper
from app.db.utils import get_or_create_async

logger = logging.getLogger(__name__)


# NUEVO: Convertido a 'async def' y usa 'AsyncSession'
async def process_movie_data(session: AsyncSession, movie_data: dict):
    """
    Valida y procesa los datos de una película, añadiéndolos a la sesión. (Async)
    """
    try:
        pydantic_movie = PydanticMovie.model_validate(movie_data)
    except Exception as e:
        movie_title = movie_data.get("titulo", "Desconocido")
        logger.warning(f"⚠️ Error de validación en la película '{movie_title}': {e}")
        raise ValueError(f"Datos de película inválidos para '{movie_title}'") from e

    db_director = None
    if pydantic_movie.director:
        director_defaults = {
            "nombre": pydantic_movie.director.nombre,
            "imagenUrl": pydantic_movie.director.imagen,
            "genero": 0,
        }
        # NUEVO: 'await' y 'get_or_create_async'
        db_director = await get_or_create_async(
            session,
            Director,
            id=pydantic_movie.director.id,
            defaults=director_defaults,
        )

    # NUEVO: Usamos asyncio.gather para ejecutar estas búsquedas en paralelo
    genre_tasks = [
        get_or_create_async(session, Genre, id=g.id, defaults=g.model_dump())
        for g in pydantic_movie.generos
    ]
    platform_tasks = [
        get_or_create_async(session, Platform, id=p.id, defaults=p.model_dump())
        for p in pydantic_movie.plataformas
    ]

    # Esperamos a que todas las tareas de géneros y plataformas terminen
    db_genres, db_platforms = await asyncio.gather(
        asyncio.gather(*genre_tasks), asyncio.gather(*platform_tasks)
    )

    db_movie = DBMovie(
        id=pydantic_movie.id,
        titulo=pydantic_movie.titulo,
        sinopsis=pydantic_movie.sinopsis,
        duracionMinutos=pydantic_movie.duracionMinutos,
        fechaEstreno=pydantic_movie.fechaEstreno,
        posterUrl=pydantic_movie.poster,
        director_id=db_director.id if db_director else None,
        activa=pydantic_movie.activa,
        generos=db_genres,
        plataformas=db_platforms,
    )
    session.add(db_movie)  # session.add() no es async

    # Procesamos el elenco
    for cast_member in pydantic_movie.elenco:
        person_defaults = {
            "nombre": cast_member.nombrePersona,
            "imagenUrl": cast_member.imagenPersona,
            "genero": 0,
        }

        # NUEVO: 'await' y 'get_or_create_async'
        db_person = await get_or_create_async(
            session, RealPerson, id=cast_member.personaId, defaults=person_defaults
        )

        # NUEVO: 'await' y 'get_or_create_async'
        await get_or_create_async(
            session,
            CastLink,
            movie_id=db_movie.id,
            person_id=db_person.id,
            defaults={
                "personaje": cast_member.personaje,
                "orden": cast_member.orden or 0,
            },
        )

    logger.info(f"✅ Película '{db_movie.titulo}' procesada y lista para guardar.")


# NUEVO: Convertido a 'async def' y usa 'AsyncSession'
async def update_movie_data(session: AsyncSession, movie_data: dict):
    """
    Actualiza los datos de una película existente. (Async)
    """
    try:
        pydantic_movie = PydanticMovie.model_validate(movie_data)
    except Exception as e:
        movie_title = movie_data.get("titulo", "Desconocido")
        logger.error(f"⚠️ Error de validación en la película '{movie_title}': {e}")
        raise ValueError(f"Datos de película inválidos para '{movie_title}'") from e

    # NUEVO: 'await session.get'
    db_movie = await session.get(DBMovie, pydantic_movie.id)
    if not db_movie:
        logger.warning(
            f"Película con ID {pydantic_movie.id} no encontrada. Creando nueva."
        )
        # NUEVO: 'await' en la llamada recursiva
        await process_movie_data(session, movie_data)
        return

    # Actualizar datos básicos
    db_movie.titulo = pydantic_movie.titulo
    db_movie.sinopsis = pydantic_movie.sinopsis
    db_movie.duracionMinutos = pydantic_movie.duracionMinutos
    db_movie.fechaEstreno = pydantic_movie.fechaEstreno
    db_movie.posterUrl = pydantic_movie.poster
    db_movie.activa = pydantic_movie.activa

    # Actualizar director
    db_director = None
    if pydantic_movie.director:
        director_defaults = {
            "nombre": pydantic_movie.director.nombre,
            "imagenUrl": pydantic_movie.director.imagen,
            "genero": 0,
        }
        # NUEVO: 'await' y 'get_or_create_async'
        db_director = await get_or_create_async(
            session,
            Director,
            id=pydantic_movie.director.id,
            defaults=director_defaults,
        )
    db_movie.director_id = db_director.id if db_director else None

    # NUEVO: Usamos asyncio.gather para actualizar relaciones en paralelo
    genre_tasks = [
        get_or_create_async(session, Genre, id=g.id, defaults=g.model_dump())
        for g in pydantic_movie.generos
    ]
    platform_tasks = [
        get_or_create_async(session, Platform, id=p.id, defaults=p.model_dump())
        for p in pydantic_movie.plataformas
    ]

    db_genres, db_platforms = await asyncio.gather(
        asyncio.gather(*genre_tasks), asyncio.gather(*platform_tasks)
    )
    db_movie.generos = db_genres
    db_movie.plataformas = db_platforms

    # Actualizar elenco
    db_movie.cast_links = []
    # NUEVO: 'await session.flush()' para aplicar el borrado de links
    await session.flush()

    for cast_member in pydantic_movie.elenco:
        person_defaults = {
            "nombre": cast_member.nombrePersona,
            "imagenUrl": cast_member.imagenPersona,
            "genero": 0,
        }
        # NUEVO: 'await' y 'get_or_create_async'
        db_person = await get_or_create_async(
            session, RealPerson, id=cast_member.personaId, defaults=person_defaults
        )

        # NUEVO: 'await' y 'get_or_create_async'
        await get_or_create_async(
            session,
            CastLink,
            movie_id=db_movie.id,
            person_id=db_person.id,
            defaults={
                "personaje": cast_member.personaje,
                "orden": cast_member.orden or 0,
            },
        )

    session.add(db_movie)
    logger.info(f"Película '{db_movie.titulo}' actualizada exitosamente.")


# NUEVO: Convertido a 'async def' y usa 'AsyncSession'
async def delete_movie_data(session: AsyncSession, movie_data: dict):
    """
    Elimina (marca como inactiva) una película. (Async)
    """
    movie_id = movie_data.get("id")
    if not movie_id:
        logger.error("No se proporcionó un ID de película para eliminar.")
        raise ValueError("ID de película requerido para eliminación")

    # NUEVO: 'await session.get'
    db_movie = await session.get(DBMovie, movie_id)
    if not db_movie:
        logger.warning(f"Película con ID {movie_id} no encontrada para eliminar.")
        return

    db_movie.activa = False
    session.add(db_movie)
    logger.info(f"Película '{db_movie.titulo}' marcada como inactiva (eliminada).")