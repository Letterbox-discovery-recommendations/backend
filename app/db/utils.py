import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import (
    AsyncSession,
)



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


# --- 5. TU FUNCIÓN HELPER 'get_or_create' (VERSIÓN ASYNC) ---
async def get_or_create_async(session: AsyncSession, model, **kwargs):
    """
    Versión asíncrona de get_or_create.
    Busca una instancia. Si no existe, la crea y la AÑADE a la sesión.
    NO hace commit.
    """
    defaults = kwargs.pop("defaults", {})

    # Usa 'await' para la ejecución de la query
    result = await session.exec(select(model).filter_by(**kwargs))
    instance = result.first()

    if instance:
        return instance
    else:
        instance_data = {**kwargs, **defaults}
        instance = model(**instance_data)
        session.add(instance)
        # No necesitas 'await' para 'session.add'
        return instance