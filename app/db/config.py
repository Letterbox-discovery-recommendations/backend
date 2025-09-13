import os
import json  # <--- 1. Importa el módulo json
from pathlib import Path  # <--- 1. Importa Path para manejar rutas
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session, select



from app.models import (
    Movie as DBMovie,
    RealPerson,
    Genre,
    Platform,
    CastLink,
    PydanticMovie
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
            session, RealPerson, id=director_data["id"], defaults=director_data
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
        fechaEstreno=pydantic_movie.fechaEstreno if pydantic_movie.fechaEstreno else None,
        posterUrl=pydantic_movie.posterUrl if pydantic_movie.posterUrl else None,
        director_id=db_director.id if db_director else None,
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

    print("Proceso de seeding completado.")

if __name__ == "__main__":
    create_db_and_tables()
    seed_initial_data()