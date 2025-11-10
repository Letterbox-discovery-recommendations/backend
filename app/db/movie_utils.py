import asyncio
import logging
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models import (
    Movie as DBMovie,
    RealPerson,
    Genre,
    Platform,
    CastLink,
    PydanticMovie,
    Director,
    MovieGenreLink,
    MoviePlatformLink,
)
from app.db.utils import get_or_create_async

logger = logging.getLogger(__name__)


# --- process_movie_data (Versión Atómica) ---
async def process_movie_data(session: AsyncSession, movie_data: dict):
    """
    Valida y procesa los datos de una película de forma atómica (Idempotente).
    Usa INSERT ... ON CONFLICT para prevenir race conditions.
    """
    try:
        pydantic_movie = PydanticMovie.model_validate(movie_data)
    except Exception as e:
        movie_title = movie_data.get("titulo", "Desconocido")
        logger.warning(f"⚠️ Error de validación en la película '{movie_title}': {e}")
        raise ValueError(f"Datos de película inválidos para '{movie_title}'") from e

    # 1. Get/create todas las entidades relacionadas (esto ya es atómico)
    db_director = None
    if pydantic_movie.director:
        director_defaults = {
            "nombre": pydantic_movie.director.nombre,
            "imagenUrl": pydantic_movie.director.imagen,
            "genero": 0,
        }
        db_director = await get_or_create_async(
            session, Director, id=pydantic_movie.director.id, defaults=director_defaults
        )

    # Creamos tareas para crear/obtener todos los géneros, plataformas y personas
    # en paralelo para máxima eficiencia.
    genre_tasks = [
        get_or_create_async(session, Genre, id=g.id, defaults=g.model_dump())
        for g in pydantic_movie.generos
    ]
    platform_tasks = [
        get_or_create_async(session, Platform, id=p.id, defaults=p.model_dump())
        for p in pydantic_movie.plataformas
    ]
    person_tasks = [
        get_or_create_async(
            session,
            RealPerson,
            id=c.personaId,
            defaults={
                "nombre": c.nombrePersona,
                "imagenUrl": c.imagenPersona,
                "genero": 0,
            },
        )
        for c in pydantic_movie.elenco
    ]

    # Ejecutamos todas las tareas
    db_genres, db_platforms, db_people = await asyncio.gather(
        asyncio.gather(*genre_tasks),
        asyncio.gather(*platform_tasks),
        asyncio.gather(*person_tasks),
    )

    # 2. Insertar atómicamente la película principal
    # No usamos session.add(), usamos un INSERT directo.
    movie_insert_stmt = (
        insert(DBMovie)
        .values(
            id=pydantic_movie.id,
            titulo=pydantic_movie.titulo,
            sinopsis=pydantic_movie.sinopsis,
            duracionMinutos=pydantic_movie.duracionMinutos,
            fechaEstreno=pydantic_movie.fechaEstreno,
            posterUrl=pydantic_movie.poster,
            director_id=db_director.id if db_director else None,
            activa=pydantic_movie.activa,
        )
        .on_conflict_do_nothing(index_elements=["id"])  # No hace nada si ya existe
    )
    await session.execute(movie_insert_stmt)  # Usar .execute()

    # 3. Insertar atómicamente las tablas de enlace (many-to-many)
    # Esto reemplaza a 'db_movie.generos = db_genres'

    # Enlaces de Género
    genre_links = [{"movie_id": pydantic_movie.id, "genre_id": g.id} for g in db_genres]
    if genre_links:
        genre_stmt = insert(MovieGenreLink).values(genre_links)
        await session.execute(
            genre_stmt.on_conflict_do_nothing(index_elements=["movie_id", "genre_id"])
        )

    # Enlaces de Plataforma
    platform_links = [
        {"movie_id": pydantic_movie.id, "platform_id": p.id} for p in db_platforms
    ]
    if platform_links:
        platform_stmt = insert(MoviePlatformLink).values(platform_links)
        await session.execute(
            platform_stmt.on_conflict_do_nothing(
                index_elements=["movie_id", "platform_id"]
            )
        )

    # Enlaces de Elenco (CastLink)
    cast_links = [
        {
            "movie_id": pydantic_movie.id,
            "person_id": person.id,
            "personaje": cast.personaje,
            "orden": cast.orden or 0,
        }
        # Mapeamos las personas devueltas por gather con los datos del elenco
        for cast, person in zip(pydantic_movie.elenco, db_people)
    ]
    if cast_links:
        cast_stmt = insert(CastLink).values(cast_links)
        await session.execute(
            cast_stmt.on_conflict_do_nothing(index_elements=["movie_id", "person_id"])
        )

    logger.info(f"✅ Película '{pydantic_movie.titulo}' procesada (atómicamente).")


# --- update_movie_data (Versión Segura) ---
async def update_movie_data(session: AsyncSession, movie_data: dict):
    """
    Actualiza los datos de una película existente.
    Esto es más complejo de hacer 100% atómico, pero podemos hacerlo seguro
    usando un bloqueo de fila.
    """
    try:
        pydantic_movie = PydanticMovie.model_validate(movie_data)
    except Exception as e:
        logger.error(f"⚠️ Error de validación en update: {e}")
        raise ValueError(f"Datos de película inválidos para update") from e

    # 1. Obtener la película (esta vez SÍ queremos bloquearla para nosotros)
    # Usamos 'session.get' con 'with_for_update' para bloquear la fila
    # Esto previene que dos 'updates' ocurran al mismo tiempo
    db_movie = await session.get(DBMovie, pydantic_movie.id, with_for_update=True)

    if not db_movie:
        logger.warning(
            f"Película con ID {pydantic_movie.id} no encontrada para actualizar. Llamando a 'crear'..."
        )
        # Si no existe, delega a la función de creación (que es atómica)
        await process_movie_data(session, movie_data)
        return

    # 2. Get/create todas las entidades relacionadas (igual que 'crear')
    db_director = None
    if pydantic_movie.director:
        db_director = await get_or_create_async(
            ...
        )  # (lógica de get_or_create_async para director)

    genre_tasks = [
        get_or_create_async(session, Genre, id=g.id, defaults=g.model_dump())
        for g in pydantic_movie.generos
    ]
    platform_tasks = [
        get_or_create_async(session, Platform, id=p.id, defaults=p.model_dump())
        for p in pydantic_movie.plataformas
    ]
    person_tasks = [
        get_or_create_async(
            session,
            RealPerson,
            id=c.personaId,
            defaults={
                "nombre": c.nombrePersona,
                "imagenUrl": c.imagenPersona,
                "genero": 0,
            },
        )
        for c in pydantic_movie.elenco
    ]

    db_genres, db_platforms, db_people = await asyncio.gather(
        asyncio.gather(*genre_tasks),
        asyncio.gather(*platform_tasks),
        asyncio.gather(*person_tasks),
    )

    # 3. Actualizar los campos simples (ya tenemos el bloqueo)
    db_movie.titulo = pydantic_movie.titulo
    db_movie.sinopsis = pydantic_movie.sinopsis
    db_movie.duracionMinutos = pydantic_movie.duracionMinutos
    db_movie.fechaEstreno = pydantic_movie.fechaEstreno
    db_movie.posterUrl = pydantic_movie.poster
    db_movie.activa = pydantic_movie.activa
    db_movie.director_id = db_director.id if db_director else None

    # 4. Actualizar relaciones (el método "borrar y recrear" es el más simple)
    #    Como tenemos la fila bloqueada, esto es seguro.

    db_movie.generos = db_genres
    db_movie.plataformas = db_platforms

    # Para CastLink, que tiene datos extra, borramos los antiguos y creamos nuevos
    db_movie.cast_links = []
    await session.flush()  # Importante: aplica el 'DELETE' de los links antiguos

    new_cast_links = [
        CastLink(
            movie_id=pydantic_movie.id,
            person_id=person.id,
            personaje=cast.personaje,
            orden=cast.orden or 0,
        )
        for cast, person in zip(pydantic_movie.elenco, db_people)
    ]
    db_movie.cast_links = new_cast_links

    # 5. Añadir el objeto actualizado (SQLModel sabe que es un UPDATE)
    session.add(db_movie)
    logger.info(f"Película '{db_movie.titulo}' actualizada exitosamente.")

# ... (delete_movie_data no cambia, ya es seguro) ...




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