from sqlmodel import Session
from app.models import (
    Movie as DBMovie,
    RealPerson,
    Genre,
    Platform,
    CastLink,
    PydanticMovie,
    Director,
)
from app.db.utils import get_or_create  # Asumiendo que utils está en app/db/utils.py
import logging

logger = logging.getLogger(__name__)


def process_movie_data(session: Session, movie_data: dict):
    """
    Valida y procesa los datos de una película, añadiéndolos a la sesión.
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        # Validamos que los datos del mensaje se ajusten a nuestro modelo Pydantic
        pydantic_movie = PydanticMovie.model_validate(movie_data)
    except Exception as e:
        movie_title = movie_data.get("titulo", "Desconocido")
        print(f"⚠️ Error de validación en la película '{movie_title}': {e}")
        # Lanzamos la excepción para que el consumidor sepa que algo falló
        raise ValueError(f"Datos de película inválidos para '{movie_title}'") from e


    db_director = None
    if pydantic_movie.director:
        director_data = pydantic_movie.director.model_dump()
        db_director = get_or_create(
            session, Director, id=director_data["id"], defaults=director_data
        )


    db_genres = [
        get_or_create(session, Genre, id=g.id, defaults=g.model_dump())
        for g in pydantic_movie.generos
    ]


    db_platforms = [
        get_or_create(session, Platform, id=p.id, defaults=p.model_dump())
        for p in pydantic_movie.plataformas
    ]


    db_movie = DBMovie(
        id=pydantic_movie.id,
        titulo=pydantic_movie.titulo,
        sinopsis=pydantic_movie.sinopsis,
        duracionMinutos=pydantic_movie.duracionMinutos,
        fechaEstreno=pydantic_movie.fechaEstreno,
        posterUrl=pydantic_movie.posterUrl,
        director_id=db_director.id if db_director else None,
        activa=pydantic_movie.activa,
        generos=db_genres,
        plataformas=db_platforms,
    )
    session.add(db_movie)


    for cast_member in pydantic_movie.elenco:

        person_data = cast_member.actor.model_dump()
        db_person = get_or_create(
            session, RealPerson, id=person_data["id"], defaults=person_data
        )
        get_or_create(
            session,
            CastLink,
            movie_id=db_movie.id,
            person_id=db_person.id,
            defaults={"personaje": cast_member.personaje, "orden": cast_member.orden},
        )

    print(f"✅ Película '{db_movie.titulo}' procesada y lista para guardar.")


def update_movie_data(session: Session, movie_data: dict):
    """
    Actualiza los datos de una película existente.
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        pydantic_movie = PydanticMovie.model_validate(movie_data)
    except Exception as e:
        movie_title = movie_data.get("titulo", "Desconocido")
        logger.error(f"⚠️ Error de validación en la película '{movie_title}': {e}")
        raise ValueError(f"Datos de película inválidos para '{movie_title}'") from e

    # Buscar la película existente
    db_movie = session.get(DBMovie, pydantic_movie.id)
    if not db_movie:
        logger.warning(f"Película con ID {pydantic_movie.id} no encontrada. Creando nueva.")
        process_movie_data(session, movie_data)
        return

    # Actualizar datos básicos
    db_movie.titulo = pydantic_movie.titulo
    db_movie.sinopsis = pydantic_movie.sinopsis
    db_movie.duracionMinutos = pydantic_movie.duracionMinutos
    db_movie.fechaEstreno = pydantic_movie.fechaEstreno
    db_movie.posterUrl = pydantic_movie.posterUrl
    db_movie.activa = pydantic_movie.activa

    # Actualizar director
    db_director = None
    if pydantic_movie.director:
        director_data = pydantic_movie.director.model_dump()
        db_director = get_or_create(
            session, Director, id=director_data["id"], defaults=director_data
        )
    db_movie.director_id = db_director.id if db_director else None

    # Actualizar géneros
    db_genres = [
        get_or_create(session, Genre, id=g.id, defaults=g.model_dump())
        for g in pydantic_movie.generos
    ]
    db_movie.generos = db_genres

    # Actualizar plataformas
    db_platforms = [
        get_or_create(session, Platform, id=p.id, defaults=p.model_dump())
        for p in pydantic_movie.plataformas
    ]
    db_movie.plataformas = db_platforms

    # Actualizar elenco - eliminar los links antiguos y crear nuevos
    db_movie.cast_links = []
    session.flush()  # Asegurar que los cambios se apliquen

    for cast_member in pydantic_movie.elenco:
        person_data = cast_member.actor.model_dump()
        db_person = get_or_create(
            session, RealPerson, id=person_data["id"], defaults=person_data
        )
        get_or_create(
            session,
            CastLink,
            movie_id=db_movie.id,
            person_id=db_person.id,
            defaults={"personaje": cast_member.personaje, "orden": cast_member.orden},
        )

    session.add(db_movie)
    logger.info(f"Película '{db_movie.titulo}' actualizada exitosamente.")


def delete_movie_data(session: Session, movie_data: dict):
    """
    Elimina (marca como inactiva) una película.
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    movie_id = movie_data.get("id")
    if not movie_id:
        logger.error("No se proporcionó un ID de película para eliminar.")
        raise ValueError("ID de película requerido para eliminación")

    db_movie = session.get(DBMovie, movie_id)
    if not db_movie:
        logger.warning(f"Película con ID {movie_id} no encontrada para eliminar.")
        return

    # Soft delete: marcar como inactiva
    db_movie.activa = False
    session.add(db_movie)
    logger.info(f"Película '{db_movie.titulo}' marcada como inactiva (eliminada).")
