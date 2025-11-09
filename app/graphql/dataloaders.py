import logging
from typing import List, Optional
from sqlalchemy import func
from sqlmodel import select
from strawberry.dataloader import DataLoader

# Importa tu fábrica de sesiones asíncronas
from app.db.utils import AsyncSessionLocal

# Importa el modelo de la base de datos que necesitamos consultar
from app.models import Review as DBReview

logger = logging.getLogger(__name__)


async def load_ratings_by_movie_ids(keys: List[int]) -> List[Optional[float]]:
    """
    Función de Dataloader para cargar los ratings promedio de películas.

    Recibe una lista de IDs de películas (keys) y debe devolver una lista
    de ratings (o None) en el MISMO orden.
    """
    logger.info(f"Dataloader: Cargando ratings para {len(keys)} películas.")

    # Si no se piden claves, devuelve una lista vacía
    if not keys:
        return []

    # 1. Crea una sesión de DB corta solo para esta operación de batch
    async with AsyncSessionLocal() as session:
        # 2. Crea UNA SOLA query para traer todos los ratings
        statement = (
            select(DBReview.movie_id, func.avg(DBReview.rating).label("avg_rating"))
            .where(DBReview.movie_id.in_(keys))
            .group_by(DBReview.movie_id)
        )

        # 3. Ejecuta la query
        results = await session.exec(statement)

        # 4. Mapea los resultados a un diccionario para acceso rápido
        #    Esto nos dará: {movie_id_1: 4.5, movie_id_2: 3.8, ...}
        ratings_map = {movie_id: avg_rating for movie_id, avg_rating in results.all()}

    # 5. Devuelve la lista en el orden exacto de las 'keys'
    #    Si una película no tiene rating (no está en el map), devuelve None.
    return [ratings_map.get(movie_id, None) for movie_id in keys]