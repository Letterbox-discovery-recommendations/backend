import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import (
    AsyncSession,
)
from sqlalchemy.dialects.postgresql import insert



from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

load_dotenv()

# --- 1. CONSTRUYE LA URL ASÍNCRONA ---
# ¡Observa el "postgresql+asyncpg"!
ASYNC_DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

# --- 2. CREA EL ENGINE ASÍNCRONO ---
# Este es el 'engine' que buscabas.
# Se crea una sola vez cuando la app inicia.
engine: AsyncEngine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para obtener una sesión de DB asíncrona.
    Maneja automáticamente el 'commit' y 'rollback'.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_engine() -> AsyncEngine:
    """Retorna la instancia del engine asíncrono."""
    return engine


async def get_or_create_async(session: AsyncSession, model, **kwargs):
    """
    Versión asíncrona y atómica de get_or_create usando
    'INSERT ... ON CONFLICT DO NOTHING'.
    Previene race conditions.
    """
    defaults = kwargs.pop("defaults", {})

    instance_data = {**kwargs, **defaults}

    insert_stmt = (
        insert(model)
        .values(**instance_data)
        .on_conflict_do_nothing(index_elements=["id"])  # Asume que 'id' es la PK
    )

    await session.execute(insert_stmt)

    instance = await session.get(model, kwargs["id"])

    return instance