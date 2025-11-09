import json
from pathlib import Path
from sqlmodel import SQLModel, Session
from .movie_utils import process_movie_data
from app.models import (
    Movie as DBMovie,
    RealPerson,
    Genre,
    Platform,
    CastLink,
    PydanticMovie,
    Director,
    Review,
    Follow,
)
from app.db.utils import engine
# Importaciones desde tu módulo de utilidades
from .utils import get_engine


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
JSON_FILE_PATH = ROOT_DIR / "peliculas.json"





async def create_db_and_tables():
    """
    Versión asíncrona que crea las tablas sin bloquear el event loop.
    """
    print("Creando tablas en la base de datos (async)...")

    # engine.run_sync() es la forma correcta de ejecutar
    # operaciones de SQLAlchemy síncronas (como create_all)
    # en un motor asíncrono.
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    print("Tablas creadas exitosamente.")






if __name__ == "__main__":
    create_db_and_tables()
