from sqlmodel.ext.asyncio.session import AsyncSession  # NUEVO: AsyncSession
from app.models import Review
import logging

logger = logging.getLogger(__name__)


# NUEVO: 'async def' y 'AsyncSession'
async def process_review_created(session: AsyncSession, review_data: dict):
    """
    Procesa la creación de una nueva reseña. (Async)
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        # Validar campos requeridos
        required_fields = ["movie_id", "user_id", "rating"]
        for field in required_fields:
            if field not in review_data:
                raise ValueError(f"Campo requerido '{field}' no encontrado en los datos de reseña")

        # Crear la reseña
        db_review = Review(
            movie_id=review_data["movie_id"],
            user_id=review_data["user_id"],
            rating=review_data["rating"],
            comment=review_data.get("comment")
        )
        session.add(db_review)  # .add() no es una operación async
        logger.info(f"Reseña creada para película {db_review.movie_id} por usuario {db_review.user_id}.")
    except Exception as e:
        logger.error(f"Error al crear reseña: {e}")
        raise ValueError(f"Error al procesar reseña") from e


# NUEVO: 'async def' y 'AsyncSession'
async def process_review_updated(session: AsyncSession, review_data: dict):
    """
    Actualiza una reseña existente. (Async)
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    review_id = review_data.get("id")
    if not review_id:
        logger.error(" No se proporcionó un ID de reseña para actualizar.")
        raise ValueError("ID de reseña requerido para actualización")

    # NUEVO: 'await' para session.get()
    db_review = await session.get(Review, review_id)
    if not db_review:
        logger.warning(f"Reseña con ID {review_id} no encontrada. Creando nueva.")
        # NUEVO: 'await' en la llamada recursiva
        await process_review_created(session, review_data)
        return

    # Actualizar campos (esto no es I/O)
    if "rating" in review_data:
        db_review.rating = review_data["rating"]
    if "comment" in review_data:
        db_review.comment = review_data["comment"]

    session.add(db_review)
    logger.info(f" Reseña con ID {review_id} actualizada exitosamente.")


# NUEVO: 'async def' y 'AsyncSession'
async def process_review_deleted(session: AsyncSession, review_data: dict):
    """
    Elimina una reseña de la base de datos. (Async)
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    review_id = review_data.get("id")
    if not review_id:
        logger.error(" No se proporcionó un ID de reseña para eliminar.")
        raise ValueError("ID de reseña requerido para eliminación")

    # NUEVO: 'await' para session.get()
    db_review = await session.get(Review, review_id)
    if not db_review:
        logger.warning(f"Reseña con ID {review_id} no encontrada para eliminar.")
        return

    # NUEVO: 'await' para session.delete()
    await session.delete(db_review)
    logger.info(f" Reseña con ID {review_id} eliminada exitosamente.")