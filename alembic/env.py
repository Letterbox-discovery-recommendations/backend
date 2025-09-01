from logging.config import fileConfig
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel
from app.models import Actor, Genre, Movie, MovieActorLink, MovieGenreLink  # noqa: F401
from sqlalchemy import engine_from_config, pool
from alembic import context

load_dotenv()


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = SQLModel.metadata


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    ...
    """
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    if not all([db_user, db_password, db_name]):
        raise ValueError(
            "Faltan variables de entorno para la base de datos (DB_USER, DB_PASSWORD, DB_NAME)"
        )

    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    print(f"\n--- Alembic se está conectando a: {DATABASE_URL} ---\n")

    connectable = engine_from_config(
        config.get_section(config.config_main_section, {}),  # type: ignore
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=DATABASE_URL,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()
