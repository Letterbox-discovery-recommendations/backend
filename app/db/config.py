import os
import json
from pathlib import Path
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session, select


from app.models import (
    Movie as DBMovie,
    RealPerson,
    Genre,
    Platform,
    CastLink,
    PydanticMovie,
    Director,
    Review
)


load_dotenv()
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    print("Creando tablas...")
    SQLModel.metadata.create_all(engine)
    print("Tablas creadas exitosamente.")


def get_or_create(session: Session, model, **kwargs):
    """
    Busca una instancia. Si no existe, la crea y la AÑADE a la sesión actual,
    pero NO hace commit. El commit se hará fuera de esta función.
    """
    defaults = kwargs.pop("defaults", {})
    instance = session.exec(select(model).filter_by(**kwargs)).first()

    if instance:
        return instance
    else:
        instance_data = {**kwargs, **defaults}
        instance = model(**instance_data)
        session.add(instance)
        return instance


# --- 2. Lógica de procesamiento adaptada para un diccionario ---
def process_movie_data(session: Session, movie_data: dict):
    """
    Valida y procesa los datos de una película, realizando un único commit al final.
    """
    try:
        pydantic_movie = PydanticMovie.model_validate(movie_data)
    except Exception as e:
        movie_title = movie_data.get("titulo", "Desconocido")
        print(f"Error validando la película '{movie_title}': {e}")
        return

    if session.get(DBMovie, pydantic_movie.id):
        print(
            f"La película '{pydantic_movie.titulo}' (ID: {pydantic_movie.id}) ya existe. Saltando."
        )
        return

    print(f"Procesando película: '{pydantic_movie.titulo}'")

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
        fechaEstreno=pydantic_movie.fechaEstreno
        if pydantic_movie.fechaEstreno
        else None,
        posterUrl=pydantic_movie.posterUrl if pydantic_movie.posterUrl else None,
        director_id=db_director.id if db_director else None,
        activa=pydantic_movie.activa if pydantic_movie.activa else None,
        generos=db_genres,
        plataformas=db_platforms,
    )
    session.add(db_movie)

    for cast_member in pydantic_movie.elenco:
        person_data = cast_member.actor.model_dump()
        db_person = get_or_create(
            session, RealPerson, id=person_data["id"], defaults=person_data
        )

        existing_link = session.exec(
            select(CastLink).filter_by(movie_id=db_movie.id, person_id=db_person.id)
        ).first()
        if not existing_link:
            cast_link = CastLink(
                movie_id=db_movie.id,
                person_id=db_person.id,
                personaje=cast_member.personaje,
                orden=cast_member.orden,
            )
            session.add(cast_link)

    session.commit()

    print(f"Película '{db_movie.titulo}' añadida exitosamente.")


# --- 3. Función principal que lee el archivo JSON ---
def seed_initial_data():
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    JSON_FILE_PATH = ROOT_DIR / "peliculas.json"
    print(JSON_FILE_PATH)
    print(ROOT_DIR)

    if not JSON_FILE_PATH.exists():
        print(f"Error: El archivo {JSON_FILE_PATH} no fue encontrado.")
        return

    print(f"Leyendo datos desde {JSON_FILE_PATH}...")
    with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
        movies_list = json.load(file)

    with Session(engine) as session:
        for movie_data in movies_list:
            process_movie_data(session, movie_data)

        # Agregar ratings mock para simular usuarios calificando películas
        mock_ratings = [
            # Ratings existentes (manteniendo compatibilidad)
            {"user_id": 1, "movie_id": 1, "rating": 5.0},
            {"user_id": 1, "movie_id": 3, "rating": 3.0},
            {"user_id": 1, "movie_id": 4, "rating": 4.0},
            {"user_id": 1, "movie_id": 5, "rating": 5.0},
            {"user_id": 2, "movie_id": 1, "rating": 4.0},
            {"user_id": 2, "movie_id": 6, "rating": 4.5},
            {"user_id": 2, "movie_id": 7, "rating": 3.5},
            {"user_id": 2, "movie_id": 8, "rating": 4.0},
            {"user_id": 3, "movie_id": 3, "rating": 4.0},
            {"user_id": 3, "movie_id": 4, "rating": 5.0},
            {"user_id": 3, "movie_id": 9, "rating": 4.5},
            {"user_id": 3, "movie_id": 10, "rating": 3.0},
            {"user_id": 3, "movie_id": 11, "rating": 4.0},
            {"user_id": 4, "movie_id": 5, "rating": 4.5},
            {"user_id": 4, "movie_id": 6, "rating": 5.0},
            {"user_id": 4, "movie_id": 14, "rating": 4.5},
            {"user_id": 5, "movie_id": 1, "rating": 4.0},
            {"user_id": 5, "movie_id": 7, "rating": 4.5},
            {"user_id": 5, "movie_id": 8, "rating": 5.0},
            {"user_id": 5, "movie_id": 9, "rating": 3.5},
            {"user_id": 5, "movie_id": 10, "rating": 4.0},
            {"user_id": 6, "movie_id": 11, "rating": 5.0},
            {"user_id": 6, "movie_id": 14, "rating": 4.5},
            {"user_id": 1, "movie_id": 6, "rating": 4.0},
            {"user_id": 2, "movie_id": 9, "rating": 4.5},
            {"user_id": 4, "movie_id": 1, "rating": 4.5},
            {"user_id": 5, "movie_id": 3, "rating": 3.5},
            {"user_id": 6, "movie_id": 5, "rating": 4.0},
            {"user_id": 7, "movie_id": 1, "rating": 2.0},
            {"user_id": 7, "movie_id": 7, "rating": 4.0},
            {"user_id": 7, "movie_id": 10, "rating": 1.5},
            {"user_id": 7, "movie_id": 14, "rating": 3.0},
            {"user_id": 8, "movie_id": 3, "rating": 5.0},
            {"user_id": 8, "movie_id": 4, "rating": 4.5},
            {"user_id": 8, "movie_id": 9, "rating": 5.0},
            {"user_id": 8, "movie_id": 11, "rating": 4.0},
            {"user_id": 9, "movie_id": 5, "rating": 2.5},
            {"user_id": 9, "movie_id": 6, "rating": 3.0},
            {"user_id": 9, "movie_id": 8, "rating": 2.0},
            {"user_id": 9, "movie_id": 14, "rating": 4.0},
            {"user_id": 9, "movie_id": 1, "rating": 3.5},
            {"user_id": 10, "movie_id": 7, "rating": 3.0},
            {"user_id": 10, "movie_id": 9, "rating": 5.0},
            {"user_id": 10, "movie_id": 10, "rating": 2.5},
            {"user_id": 1, "movie_id": 9, "rating": 4.5},
            {"user_id": 3, "movie_id": 5, "rating": 4.0},
            {"user_id": 4, "movie_id": 8, "rating": 4.5},
            {"user_id": 5, "movie_id": 11, "rating": 3.0},
            {"user_id": 6, "movie_id": 7, "rating": 4.5},
            {"user_id": 7, "movie_id": 4, "rating": 2.5},
            {"user_id": 8, "movie_id": 6, "rating": 4.0},
            {"user_id": 10, "movie_id": 1, "rating": 5.0},
            {"user_id": 11, "movie_id": 15, "rating": 4.5},
            {"user_id": 11, "movie_id": 16, "rating": 5.0},
            {"user_id": 11, "movie_id": 17, "rating": 3.5},
            {"user_id": 11, "movie_id": 18, "rating": 4.0},
            {"user_id": 11, "movie_id": 19, "rating": 2.0},
            {"user_id": 12, "movie_id": 1, "rating": 2.5},
            {"user_id": 12, "movie_id": 5, "rating": 3.0},
            {"user_id": 12, "movie_id": 10, "rating": 2.0},
            {"user_id": 12, "movie_id": 15, "rating": 1.5},
            {"user_id": 12, "movie_id": 20, "rating": 3.5},
            {"user_id": 13, "movie_id": 6, "rating": 5.0},
            {"user_id": 13, "movie_id": 8, "rating": 4.5},
            {"user_id": 13, "movie_id": 16, "rating": 4.0},
            {"user_id": 13, "movie_id": 18, "rating": 4.5},
            {"user_id": 14, "movie_id": 7, "rating": 5.0},
            {"user_id": 14, "movie_id": 9, "rating": 3.0},
            {"user_id": 14, "movie_id": 14, "rating": 4.5},
            {"user_id": 14, "movie_id": 17, "rating": 2.5},
            {"user_id": 15, "movie_id": 1, "rating": 5.0},
            {"user_id": 15, "movie_id": 3, "rating": 4.5},
            {"user_id": 15, "movie_id": 4, "rating": 5.0},
            {"user_id": 15, "movie_id": 11, "rating": 4.0},
            {"user_id": 11, "movie_id": 3, "rating": 4.0},
            {"user_id": 12, "movie_id": 7, "rating": 2.5},
            {"user_id": 13, "movie_id": 9, "rating": 4.5},
            {"user_id": 14, "movie_id": 11, "rating": 3.5},
            {"user_id": 15, "movie_id": 6, "rating": 4.0},
            {"user_id": 1, "movie_id": 15, "rating": 4.5},
            {"user_id": 2, "movie_id": 16, "rating": 3.0},
            {"user_id": 3, "movie_id": 17, "rating": 4.0},
            {"user_id": 4, "movie_id": 18, "rating": 2.5},
            {"user_id": 5, "movie_id": 19, "rating": 4.5},
            {"user_id": 6, "movie_id": 20, "rating": 3.5},
            {"user_id": 7, "movie_id": 15, "rating": 2.0},
            {"user_id": 8, "movie_id": 16, "rating": 4.5},
            {"user_id": 9, "movie_id": 17, "rating": 3.0},
            {"user_id": 10, "movie_id": 18, "rating": 4.0},
            
            # Nuevos ratings mock variados y extensos
            {"user_id": 1, "movie_id": 21, "rating": 4.0},
            {"user_id": 1, "movie_id": 22, "rating": 3.5},
            {"user_id": 1, "movie_id": 23, "rating": 5.0},
            {"user_id": 1, "movie_id": 24, "rating": 2.5},
            {"user_id": 1, "movie_id": 25, "rating": 4.5},
            {"user_id": 1, "movie_id": 26, "rating": 3.0},
            {"user_id": 1, "movie_id": 27, "rating": 4.0},
            {"user_id": 1, "movie_id": 28, "rating": 5.0},
            {"user_id": 1, "movie_id": 30, "rating": 4.5},
            {"user_id": 2, "movie_id": 21, "rating": 3.5},
            {"user_id": 2, "movie_id": 22, "rating": 4.0},
            {"user_id": 2, "movie_id": 23, "rating": 4.5},
            {"user_id": 2, "movie_id": 24, "rating": 3.0},
            {"user_id": 2, "movie_id": 25, "rating": 5.0},
            {"user_id": 2, "movie_id": 26, "rating": 2.5},
            {"user_id": 2, "movie_id": 27, "rating": 4.0},
            {"user_id": 2, "movie_id": 28, "rating": 3.5},
            {"user_id": 2, "movie_id": 30, "rating": 1.5},
            {"user_id": 3, "movie_id": 21, "rating": 4.5},
            {"user_id": 3, "movie_id": 22, "rating": 3.0},
            {"user_id": 3, "movie_id": 23, "rating": 5.0},
            {"user_id": 3, "movie_id": 24, "rating": 4.0},
            {"user_id": 3, "movie_id": 25, "rating": 2.5},
            {"user_id": 3, "movie_id": 26, "rating": 4.5},
            {"user_id": 3, "movie_id": 27, "rating": 3.5},
            {"user_id": 3, "movie_id": 28, "rating": 4.0},
            {"user_id": 3, "movie_id": 30, "rating": 2.0},
            {"user_id": 4, "movie_id": 21, "rating": 3.0},
            {"user_id": 4, "movie_id": 22, "rating": 4.5},
            {"user_id": 4, "movie_id": 23, "rating": 4.0},
            {"user_id": 4, "movie_id": 24, "rating": 5.0},
            {"user_id": 4, "movie_id": 25, "rating": 3.5},
            {"user_id": 4, "movie_id": 26, "rating": 2.0},
            {"user_id": 4, "movie_id": 27, "rating": 4.5},
            {"user_id": 4, "movie_id": 28, "rating": 3.0},
            {"user_id": 4, "movie_id": 30, "rating": 5.0},
            {"user_id": 5, "movie_id": 21, "rating": 4.0},
            {"user_id": 5, "movie_id": 22, "rating": 5.0},
            {"user_id": 5, "movie_id": 23, "rating": 3.5},
            {"user_id": 5, "movie_id": 24, "rating": 2.5},
            {"user_id": 5, "movie_id": 25, "rating": 4.5},
            {"user_id": 5, "movie_id": 26, "rating": 4.0},
            {"user_id": 5, "movie_id": 27, "rating": 3.0},
            {"user_id": 5, "movie_id": 28, "rating": 4.5},
            {"user_id": 5, "movie_id": 30, "rating": 2.0},
            {"user_id": 6, "movie_id": 21, "rating": 2.5},
            {"user_id": 6, "movie_id": 22, "rating": 4.0},
            {"user_id": 6, "movie_id": 23, "rating": 4.5},
            {"user_id": 6, "movie_id": 24, "rating": 3.5},
            {"user_id": 6, "movie_id": 25, "rating": 5.0},
            {"user_id": 6, "movie_id": 26, "rating": 3.0},
            {"user_id": 6, "movie_id": 27, "rating": 4.0},
            {"user_id": 6, "movie_id": 28, "rating": 2.5},
            {"user_id": 6, "movie_id": 30, "rating": 3.5},
            {"user_id": 7, "movie_id": 21, "rating": 4.5},
            {"user_id": 7, "movie_id": 22, "rating": 3.0},
            {"user_id": 7, "movie_id": 23, "rating": 5.0},
            {"user_id": 7, "movie_id": 24, "rating": 4.0},
            {"user_id": 7, "movie_id": 25, "rating": 2.0},
            {"user_id": 7, "movie_id": 26, "rating": 4.5},
            {"user_id": 7, "movie_id": 27, "rating": 3.5},
            {"user_id": 7, "movie_id": 28, "rating": 4.0},
            {"user_id": 7, "movie_id": 30, "rating": 5.0},
            {"user_id": 8, "movie_id": 21, "rating": 3.5},
            {"user_id": 8, "movie_id": 22, "rating": 4.0},
            {"user_id": 8, "movie_id": 23, "rating": 4.5},
            {"user_id": 8, "movie_id": 24, "rating": 2.5},
            {"user_id": 8, "movie_id": 25, "rating": 3.0},
            {"user_id": 8, "movie_id": 26, "rating": 4.5},
            {"user_id": 8, "movie_id": 27, "rating": 5.0},
            {"user_id": 8, "movie_id": 28, "rating": 3.5},
            {"user_id": 8, "movie_id": 30, "rating": 2.0},
            {"user_id": 9, "movie_id": 21, "rating": 4.0},
            {"user_id": 9, "movie_id": 22, "rating": 5.0},
            {"user_id": 9, "movie_id": 23, "rating": 3.0},
            {"user_id": 9, "movie_id": 24, "rating": 4.5},
            {"user_id": 9, "movie_id": 25, "rating": 2.5},
            {"user_id": 9, "movie_id": 26, "rating": 4.0},
            {"user_id": 9, "movie_id": 27, "rating": 3.5},
            {"user_id": 9, "movie_id": 28, "rating": 4.5},
            {"user_id": 9, "movie_id": 30, "rating": 1.0},
            {"user_id": 10, "movie_id": 21, "rating": 2.0},
            {"user_id": 10, "movie_id": 22, "rating": 4.5},
            {"user_id": 10, "movie_id": 23, "rating": 4.0},
            {"user_id": 10, "movie_id": 24, "rating": 3.5},
            {"user_id": 10, "movie_id": 25, "rating": 5.0},
            {"user_id": 10, "movie_id": 26, "rating": 3.0},
            {"user_id": 10, "movie_id": 27, "rating": 4.0},
            {"user_id": 10, "movie_id": 28, "rating": 2.5},
            {"user_id": 10, "movie_id": 30, "rating": 3.5},
            {"user_id": 11, "movie_id": 21, "rating": 4.5},
            {"user_id": 11, "movie_id": 22, "rating": 3.5},
            {"user_id": 11, "movie_id": 23, "rating": 4.0},
            {"user_id": 11, "movie_id": 24, "rating": 5.0},
            {"user_id": 11, "movie_id": 25, "rating": 2.5},
            {"user_id": 11, "movie_id": 26, "rating": 4.0},
            {"user_id": 11, "movie_id": 27, "rating": 3.0},
            {"user_id": 11, "movie_id": 28, "rating": 4.5},
            {"user_id": 11, "movie_id": 30, "rating": 2.0},
            {"user_id": 12, "movie_id": 21, "rating": 3.0},
            {"user_id": 12, "movie_id": 22, "rating": 4.0},
            {"user_id": 12, "movie_id": 23, "rating": 4.5},
            {"user_id": 12, "movie_id": 24, "rating": 2.0},
            {"user_id": 12, "movie_id": 25, "rating": 3.5},
            {"user_id": 12, "movie_id": 26, "rating": 4.5},
            {"user_id": 12, "movie_id": 27, "rating": 5.0},
            {"user_id": 12, "movie_id": 28, "rating": 3.0},
            {"user_id": 12, "movie_id": 30, "rating": 2.5},
            {"user_id": 13, "movie_id": 21, "rating": 4.0},
            {"user_id": 13, "movie_id": 22, "rating": 5.0},
            {"user_id": 13, "movie_id": 23, "rating": 3.5},
            {"user_id": 13, "movie_id": 24, "rating": 4.5},
            {"user_id": 13, "movie_id": 25, "rating": 2.0},
            {"user_id": 13, "movie_id": 26, "rating": 4.0},
            {"user_id": 13, "movie_id": 27, "rating": 3.5},
            {"user_id": 13, "movie_id": 28, "rating": 4.5},
            {"user_id": 13, "movie_id": 30, "rating": 1.5},
            {"user_id": 14, "movie_id": 21, "rating": 2.5},
            {"user_id": 14, "movie_id": 22, "rating": 4.5},
            {"user_id": 14, "movie_id": 23, "rating": 4.0},
            {"user_id": 14, "movie_id": 24, "rating": 3.0},
            {"user_id": 14, "movie_id": 25, "rating": 5.0},
            {"user_id": 14, "movie_id": 26, "rating": 3.5},
            {"user_id": 14, "movie_id": 27, "rating": 4.0},
            {"user_id": 14, "movie_id": 28, "rating": 2.0},
            {"user_id": 14, "movie_id": 30, "rating": 3.0},
            {"user_id": 15, "movie_id": 21, "rating": 4.5},
            {"user_id": 15, "movie_id": 22, "rating": 3.0},
            {"user_id": 15, "movie_id": 23, "rating": 5.0},
            {"user_id": 15, "movie_id": 24, "rating": 4.0},
            {"user_id": 15, "movie_id": 25, "rating": 2.5},
            {"user_id": 15, "movie_id": 26, "rating": 4.5},
            {"user_id": 15, "movie_id": 27, "rating": 3.5},
            {"user_id": 15, "movie_id": 28, "rating": 4.0},
            {"user_id": 15, "movie_id": 30, "rating": 2.0},
            
            # Más películas (31-60)
            {"user_id": 1, "movie_id": 31, "rating": 4.0},
            {"user_id": 1, "movie_id": 32, "rating": 3.5},
            {"user_id": 1, "movie_id": 33, "rating": 5.0},
            {"user_id": 1, "movie_id": 34, "rating": 2.5},
            {"user_id": 1, "movie_id": 35, "rating": 4.5},
            {"user_id": 2, "movie_id": 31, "rating": 3.0},
            {"user_id": 2, "movie_id": 32, "rating": 4.0},
            {"user_id": 2, "movie_id": 33, "rating": 4.5},
            {"user_id": 2, "movie_id": 34, "rating": 2.0},
            {"user_id": 2, "movie_id": 35, "rating": 5.0},
            {"user_id": 3, "movie_id": 31, "rating": 4.5},
            {"user_id": 3, "movie_id": 32, "rating": 3.0},
            {"user_id": 3, "movie_id": 33, "rating": 5.0},
            {"user_id": 3, "movie_id": 34, "rating": 4.0},
            {"user_id": 3, "movie_id": 35, "rating": 2.5},
            {"user_id": 4, "movie_id": 31, "rating": 3.5},
            {"user_id": 4, "movie_id": 32, "rating": 4.5},
            {"user_id": 4, "movie_id": 33, "rating": 4.0},
            {"user_id": 4, "movie_id": 34, "rating": 5.0},
            {"user_id": 4, "movie_id": 35, "rating": 3.0},
            {"user_id": 5, "movie_id": 31, "rating": 4.0},
            {"user_id": 5, "movie_id": 32, "rating": 5.0},
            {"user_id": 5, "movie_id": 33, "rating": 3.5},
            {"user_id": 5, "movie_id": 34, "rating": 2.5},
            {"user_id": 5, "movie_id": 35, "rating": 4.5},
            {"user_id": 6, "movie_id": 31, "rating": 2.0},
            {"user_id": 6, "movie_id": 32, "rating": 4.0},
            {"user_id": 6, "movie_id": 33, "rating": 4.5},
            {"user_id": 6, "movie_id": 34, "rating": 3.5},
            {"user_id": 6, "movie_id": 35, "rating": 5.0},
            {"user_id": 7, "movie_id": 31, "rating": 4.5},
            {"user_id": 7, "movie_id": 32, "rating": 3.0},
            {"user_id": 7, "movie_id": 33, "rating": 5.0},
            {"user_id": 7, "movie_id": 34, "rating": 4.0},
            {"user_id": 7, "movie_id": 35, "rating": 2.0},
            {"user_id": 8, "movie_id": 31, "rating": 3.0},
            {"user_id": 8, "movie_id": 32, "rating": 4.5},
            {"user_id": 8, "movie_id": 33, "rating": 4.0},
            {"user_id": 8, "movie_id": 34, "rating": 2.5},
            {"user_id": 8, "movie_id": 35, "rating": 3.5},
            {"user_id": 9, "movie_id": 31, "rating": 4.0},
            {"user_id": 9, "movie_id": 32, "rating": 5.0},
            {"user_id": 9, "movie_id": 33, "rating": 3.0},
            {"user_id": 9, "movie_id": 34, "rating": 4.5},
            {"user_id": 9, "movie_id": 35, "rating": 2.5},
            {"user_id": 10, "movie_id": 31, "rating": 2.5},
            {"user_id": 10, "movie_id": 32, "rating": 4.0},
            {"user_id": 10, "movie_id": 33, "rating": 4.5},
            {"user_id": 10, "movie_id": 34, "rating": 3.0},
            {"user_id": 10, "movie_id": 35, "rating": 5.0},
            {"user_id": 11, "movie_id": 31, "rating": 4.5},
            {"user_id": 11, "movie_id": 32, "rating": 3.5},
            {"user_id": 11, "movie_id": 33, "rating": 4.0},
            {"user_id": 11, "movie_id": 34, "rating": 5.0},
            {"user_id": 11, "movie_id": 35, "rating": 2.0},
            {"user_id": 12, "movie_id": 31, "rating": 3.0},
            {"user_id": 12, "movie_id": 32, "rating": 4.0},
            {"user_id": 12, "movie_id": 33, "rating": 4.5},
            {"user_id": 12, "movie_id": 34, "rating": 2.5},
            {"user_id": 12, "movie_id": 35, "rating": 3.5},
            {"user_id": 13, "movie_id": 31, "rating": 4.0},
            {"user_id": 13, "movie_id": 32, "rating": 5.0},
            {"user_id": 13, "movie_id": 33, "rating": 3.5},
            {"user_id": 13, "movie_id": 34, "rating": 4.5},
            {"user_id": 13, "movie_id": 35, "rating": 2.0},
            {"user_id": 14, "movie_id": 31, "rating": 2.5},
            {"user_id": 14, "movie_id": 32, "rating": 4.5},
            {"user_id": 14, "movie_id": 33, "rating": 4.0},
            {"user_id": 14, "movie_id": 34, "rating": 3.0},
            {"user_id": 14, "movie_id": 35, "rating": 5.0},
            {"user_id": 15, "movie_id": 31, "rating": 4.5},
            {"user_id": 15, "movie_id": 32, "rating": 3.0},
            {"user_id": 15, "movie_id": 33, "rating": 5.0},
            {"user_id": 15, "movie_id": 34, "rating": 4.0},
            {"user_id": 15, "movie_id": 35, "rating": 2.5},
            
            # Películas 36-50 con variedad adicional
            {"user_id": 1, "movie_id": 36, "rating": 3.5},
            {"user_id": 1, "movie_id": 37, "rating": 4.0},
            {"user_id": 1, "movie_id": 38, "rating": 2.0},
            {"user_id": 1, "movie_id": 39, "rating": 4.5},
            {"user_id": 1, "movie_id": 40, "rating": 5.0},
            {"user_id": 2, "movie_id": 36, "rating": 4.0},
            {"user_id": 2, "movie_id": 37, "rating": 3.5},
            {"user_id": 2, "movie_id": 38, "rating": 4.5},
            {"user_id": 2, "movie_id": 39, "rating": 2.5},
            {"user_id": 2, "movie_id": 40, "rating": 3.0},
            {"user_id": 3, "movie_id": 36, "rating": 5.0},
            {"user_id": 3, "movie_id": 37, "rating": 4.0},
            {"user_id": 3, "movie_id": 38, "rating": 3.5},
            {"user_id": 3, "movie_id": 39, "rating": 4.5},
            {"user_id": 3, "movie_id": 40, "rating": 2.0},
            {"user_id": 4, "movie_id": 36, "rating": 2.5},
            {"user_id": 4, "movie_id": 37, "rating": 4.5},
            {"user_id": 4, "movie_id": 38, "rating": 4.0},
            {"user_id": 4, "movie_id": 39, "rating": 5.0},
            {"user_id": 4, "movie_id": 40, "rating": 3.5},
            {"user_id": 5, "movie_id": 36, "rating": 4.0},
            {"user_id": 5, "movie_id": 37, "rating": 5.0},
            {"user_id": 5, "movie_id": 38, "rating": 3.0},
            {"user_id": 5, "movie_id": 39, "rating": 2.5},
            {"user_id": 5, "movie_id": 40, "rating": 4.5},
            {"user_id": 6, "movie_id": 36, "rating": 3.5},
            {"user_id": 6, "movie_id": 37, "rating": 4.0},
            {"user_id": 6, "movie_id": 38, "rating": 5.0},
            {"user_id": 6, "movie_id": 39, "rating": 2.0},
            {"user_id": 6, "movie_id": 40, "rating": 4.5},
            {"user_id": 7, "movie_id": 36, "rating": 4.5},
            {"user_id": 7, "movie_id": 37, "rating": 3.0},
            {"user_id": 7, "movie_id": 38, "rating": 4.0},
            {"user_id": 7, "movie_id": 39, "rating": 5.0},
            {"user_id": 7, "movie_id": 40, "rating": 1.5},
            {"user_id": 8, "movie_id": 36, "rating": 2.0},
            {"user_id": 8, "movie_id": 37, "rating": 4.5},
            {"user_id": 8, "movie_id": 38, "rating": 4.0},
            {"user_id": 8, "movie_id": 39, "rating": 3.5},
            {"user_id": 8, "movie_id": 40, "rating": 5.0},
            {"user_id": 9, "movie_id": 36, "rating": 4.0},
            {"user_id": 9, "movie_id": 37, "rating": 5.0},
            {"user_id": 9, "movie_id": 38, "rating": 2.5},
            {"user_id": 9, "movie_id": 39, "rating": 4.5},
            {"user_id": 9, "movie_id": 40, "rating": 3.0},
            {"user_id": 10, "movie_id": 36, "rating": 3.5},
            {"user_id": 10, "movie_id": 37, "rating": 4.0},
            {"user_id": 10, "movie_id": 38, "rating": 4.5},
            {"user_id": 10, "movie_id": 39, "rating": 2.0},
            {"user_id": 10, "movie_id": 40, "rating": 5.0},
            {"user_id": 11, "movie_id": 36, "rating": 4.5},
            {"user_id": 11, "movie_id": 37, "rating": 3.5},
            {"user_id": 11, "movie_id": 38, "rating": 4.0},
            {"user_id": 11, "movie_id": 39, "rating": 5.0},
            {"user_id": 11, "movie_id": 40, "rating": 2.5},
            {"user_id": 12, "movie_id": 36, "rating": 2.0},
            {"user_id": 12, "movie_id": 37, "rating": 4.0},
            {"user_id": 12, "movie_id": 38, "rating": 4.5},
            {"user_id": 12, "movie_id": 39, "rating": 3.0},
            {"user_id": 12, "movie_id": 40, "rating": 5.0},
            {"user_id": 13, "movie_id": 36, "rating": 4.0},
            {"user_id": 13, "movie_id": 37, "rating": 5.0},
            {"user_id": 13, "movie_id": 38, "rating": 3.5},
            {"user_id": 13, "movie_id": 39, "rating": 4.5},
            {"user_id": 13, "movie_id": 40, "rating": 2.0},
            {"user_id": 14, "movie_id": 36, "rating": 3.0},
            {"user_id": 14, "movie_id": 37, "rating": 4.5},
            {"user_id": 14, "movie_id": 38, "rating": 4.0},
            {"user_id": 14, "movie_id": 39, "rating": 2.5},
            {"user_id": 14, "movie_id": 40, "rating": 5.0},
            {"user_id": 15, "movie_id": 36, "rating": 4.5},
            {"user_id": 15, "movie_id": 37, "rating": 3.0},
            {"user_id": 15, "movie_id": 38, "rating": 5.0},
            {"user_id": 15, "movie_id": 39, "rating": 4.0},
            {"user_id": 15, "movie_id": 40, "rating": 2.5},
            
            # Películas 41-50
            {"user_id": 1, "movie_id": 41, "rating": 4.0},
            {"user_id": 1, "movie_id": 42, "rating": 3.5},
            {"user_id": 1, "movie_id": 43, "rating": 5.0},
            {"user_id": 1, "movie_id": 44, "rating": 2.5},
            {"user_id": 1, "movie_id": 45, "rating": 4.5},
            {"user_id": 2, "movie_id": 41, "rating": 3.0},
            {"user_id": 2, "movie_id": 42, "rating": 4.0},
            {"user_id": 2, "movie_id": 43, "rating": 4.5},
            {"user_id": 2, "movie_id": 44, "rating": 2.0},
            {"user_id": 2, "movie_id": 45, "rating": 5.0},
            {"user_id": 3, "movie_id": 41, "rating": 4.5},
            {"user_id": 3, "movie_id": 42, "rating": 3.0},
            {"user_id": 3, "movie_id": 43, "rating": 5.0},
            {"user_id": 3, "movie_id": 44, "rating": 4.0},
            {"user_id": 3, "movie_id": 45, "rating": 2.5},
            {"user_id": 4, "movie_id": 41, "rating": 2.5},
            {"user_id": 4, "movie_id": 42, "rating": 4.5},
            {"user_id": 4, "movie_id": 43, "rating": 4.0},
            {"user_id": 4, "movie_id": 44, "rating": 5.0},
            {"user_id": 4, "movie_id": 45, "rating": 3.0},
            {"user_id": 5, "movie_id": 41, "rating": 4.0},
            {"user_id": 5, "movie_id": 42, "rating": 5.0},
            {"user_id": 5, "movie_id": 43, "rating": 3.5},
            {"user_id": 5, "movie_id": 44, "rating": 2.5},
            {"user_id": 5, "movie_id": 45, "rating": 4.5},
            {"user_id": 6, "movie_id": 41, "rating": 3.5},
            {"user_id": 6, "movie_id": 42, "rating": 4.0},
            {"user_id": 6, "movie_id": 43, "rating": 4.5},
            {"user_id": 6, "movie_id": 44, "rating": 2.0},
            {"user_id": 6, "movie_id": 45, "rating": 5.0},
            {"user_id": 7, "movie_id": 41, "rating": 4.5},
            {"user_id": 7, "movie_id": 42, "rating": 3.0},
            {"user_id": 7, "movie_id": 43, "rating": 5.0},
            {"user_id": 7, "movie_id": 44, "rating": 4.0},
            {"user_id": 7, "movie_id": 45, "rating": 2.0},
            {"user_id": 8, "movie_id": 41, "rating": 2.0},
            {"user_id": 8, "movie_id": 42, "rating": 4.5},
            {"user_id": 8, "movie_id": 43, "rating": 4.0},
            {"user_id": 8, "movie_id": 44, "rating": 3.5},
            {"user_id": 8, "movie_id": 45, "rating": 5.0},
            {"user_id": 9, "movie_id": 41, "rating": 4.0},
            {"user_id": 9, "movie_id": 42, "rating": 5.0},
            {"user_id": 9, "movie_id": 43, "rating": 2.5},
            {"user_id": 9, "movie_id": 44, "rating": 4.5},
            {"user_id": 9, "movie_id": 45, "rating": 3.0},
            {"user_id": 10, "movie_id": 41, "rating": 3.5},
            {"user_id": 10, "movie_id": 42, "rating": 4.0},
            {"user_id": 10, "movie_id": 43, "rating": 4.5},
            {"user_id": 10, "movie_id": 44, "rating": 2.0},
            {"user_id": 10, "movie_id": 45, "rating": 5.0},
            {"user_id": 11, "movie_id": 41, "rating": 4.5},
            {"user_id": 11, "movie_id": 42, "rating": 3.5},
            {"user_id": 11, "movie_id": 43, "rating": 4.0},
            {"user_id": 11, "movie_id": 44, "rating": 5.0},
            {"user_id": 11, "movie_id": 45, "rating": 2.5},
            {"user_id": 12, "movie_id": 41, "rating": 2.0},
            {"user_id": 12, "movie_id": 42, "rating": 4.0},
            {"user_id": 12, "movie_id": 43, "rating": 4.5},
            {"user_id": 12, "movie_id": 44, "rating": 3.0},
            {"user_id": 12, "movie_id": 45, "rating": 5.0},
            {"user_id": 13, "movie_id": 41, "rating": 4.0},
            {"user_id": 13, "movie_id": 42, "rating": 5.0},
            {"user_id": 13, "movie_id": 43, "rating": 3.5},
            {"user_id": 13, "movie_id": 44, "rating": 4.5},
            {"user_id": 13, "movie_id": 45, "rating": 2.0},
            {"user_id": 14, "movie_id": 41, "rating": 3.0},
            {"user_id": 14, "movie_id": 42, "rating": 4.5},
            {"user_id": 14, "movie_id": 43, "rating": 4.0},
            {"user_id": 14, "movie_id": 44, "rating": 2.5},
            {"user_id": 14, "movie_id": 45, "rating": 5.0},
            {"user_id": 15, "movie_id": 41, "rating": 4.5},
            {"user_id": 15, "movie_id": 42, "rating": 3.0},
            {"user_id": 15, "movie_id": 43, "rating": 5.0},
            {"user_id": 15, "movie_id": 44, "rating": 4.0},
            {"user_id": 15, "movie_id": 45, "rating": 2.5},
            
            # Películas 46-50
            {"user_id": 1, "movie_id": 46, "rating": 3.5},
            {"user_id": 1, "movie_id": 47, "rating": 4.0},
            {"user_id": 1, "movie_id": 48, "rating": 2.0},
            {"user_id": 1, "movie_id": 49, "rating": 4.5},
            {"user_id": 1, "movie_id": 50, "rating": 5.0},
            {"user_id": 2, "movie_id": 46, "rating": 4.0},
            {"user_id": 2, "movie_id": 47, "rating": 3.5},
            {"user_id": 2, "movie_id": 48, "rating": 4.5},
            {"user_id": 2, "movie_id": 49, "rating": 2.5},
            {"user_id": 2, "movie_id": 50, "rating": 3.0},
            {"user_id": 3, "movie_id": 46, "rating": 5.0},
            {"user_id": 3, "movie_id": 47, "rating": 4.0},
            {"user_id": 3, "movie_id": 48, "rating": 3.5},
            {"user_id": 3, "movie_id": 49, "rating": 4.5},
            {"user_id": 3, "movie_id": 50, "rating": 2.0},
            {"user_id": 4, "movie_id": 46, "rating": 2.5},
            {"user_id": 4, "movie_id": 47, "rating": 4.5},
            {"user_id": 4, "movie_id": 48, "rating": 4.0},
            {"user_id": 4, "movie_id": 49, "rating": 5.0},
            {"user_id": 4, "movie_id": 50, "rating": 3.5},
            {"user_id": 5, "movie_id": 46, "rating": 4.0},
            {"user_id": 5, "movie_id": 47, "rating": 5.0},
            {"user_id": 5, "movie_id": 48, "rating": 3.0},
            {"user_id": 5, "movie_id": 49, "rating": 2.5},
            {"user_id": 5, "movie_id": 50, "rating": 4.5},
            {"user_id": 6, "movie_id": 46, "rating": 3.5},
            {"user_id": 6, "movie_id": 47, "rating": 4.0},
            {"user_id": 6, "movie_id": 48, "rating": 5.0},
            {"user_id": 6, "movie_id": 49, "rating": 2.0},
            {"user_id": 6, "movie_id": 50, "rating": 4.5},
            {"user_id": 7, "movie_id": 46, "rating": 4.5},
            {"user_id": 7, "movie_id": 47, "rating": 3.0},
            {"user_id": 7, "movie_id": 48, "rating": 4.0},
            {"user_id": 7, "movie_id": 49, "rating": 5.0},
            {"user_id": 7, "movie_id": 50, "rating": 1.5},
            {"user_id": 8, "movie_id": 46, "rating": 2.0},
            {"user_id": 8, "movie_id": 47, "rating": 4.5},
            {"user_id": 8, "movie_id": 48, "rating": 4.0},
            {"user_id": 8, "movie_id": 49, "rating": 3.5},
            {"user_id": 8, "movie_id": 50, "rating": 5.0},
            {"user_id": 9, "movie_id": 46, "rating": 4.0},
            {"user_id": 9, "movie_id": 47, "rating": 5.0},
            {"user_id": 9, "movie_id": 48, "rating": 2.5},
            {"user_id": 9, "movie_id": 49, "rating": 4.5},
            {"user_id": 9, "movie_id": 50, "rating": 3.0},
            {"user_id": 10, "movie_id": 46, "rating": 3.5},
            {"user_id": 10, "movie_id": 47, "rating": 4.0},
            {"user_id": 10, "movie_id": 48, "rating": 4.5},
            {"user_id": 10, "movie_id": 49, "rating": 2.0},
            {"user_id": 10, "movie_id": 50, "rating": 5.0},
            {"user_id": 11, "movie_id": 46, "rating": 4.5},
            {"user_id": 11, "movie_id": 47, "rating": 3.5},
            {"user_id": 11, "movie_id": 48, "rating": 4.0},
            {"user_id": 11, "movie_id": 49, "rating": 5.0},
            {"user_id": 11, "movie_id": 50, "rating": 2.5},
            {"user_id": 12, "movie_id": 46, "rating": 2.0},
            {"user_id": 12, "movie_id": 47, "rating": 4.0},
            {"user_id": 12, "movie_id": 48, "rating": 4.5},
            {"user_id": 12, "movie_id": 49, "rating": 3.0},
            {"user_id": 12, "movie_id": 50, "rating": 5.0},
            {"user_id": 13, "movie_id": 46, "rating": 4.0},
            {"user_id": 13, "movie_id": 47, "rating": 5.0},
            {"user_id": 13, "movie_id": 48, "rating": 3.5},
            {"user_id": 13, "movie_id": 49, "rating": 4.5},
            {"user_id": 13, "movie_id": 50, "rating": 2.0},
            {"user_id": 14, "movie_id": 46, "rating": 3.0},
            {"user_id": 14, "movie_id": 47, "rating": 4.5},
            {"user_id": 14, "movie_id": 48, "rating": 4.0},
            {"user_id": 14, "movie_id": 49, "rating": 2.5},
            {"user_id": 14, "movie_id": 50, "rating": 5.0},
            {"user_id": 15, "movie_id": 46, "rating": 4.5},
            {"user_id": 15, "movie_id": 47, "rating": 3.0},
            {"user_id": 15, "movie_id": 48, "rating": 5.0},
            {"user_id": 15, "movie_id": 49, "rating": 4.0},
            {"user_id": 15, "movie_id": 50, "rating": 2.5},
        ]
        
        for rating_data in mock_ratings:
            review = Review(**rating_data)
            session.add(review)
        
        session.commit()
        print("Ratings mock agregados.")

    print("Proceso de seeding completado.")


if __name__ == "__main__":
    create_db_and_tables()
    seed_initial_data()
