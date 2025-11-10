from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Review
import logging

# NUEVO: Importar 'insert' de PostgreSQL
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)


async def process_review_created(session: AsyncSession, review_data: dict):
    """
    Procesa la creación (o actualización) de una nueva reseña de forma atómica.
    Usa 'INSERT ... ON CONFLICT DO UPDATE' para ser idempotente.
    """
    try:
        # Validar campos requeridos
        required_fields = ["movie_id", "user_id", "rating"]
        for field in required_fields:
            if field not in review_data:
                raise ValueError(f"Campo requerido '{field}' no encontrado")

        # 1. Preparar los datos
        review_values = {
            "movie_id": review_data["movie_id"],
            "user_id": review_data["user_id"],
            "rating": review_data["rating"],
            "comment": review_data.get("comment"),
        }

        # 2. Crear el statement 'UPSERT' (Insertar o Actualizar)
        insert_stmt = (
            insert(Review)
            .values(**review_values)
            .on_conflict_do_update(
                # Asume que tu 'UNIQUE constraint' es en estas dos columnas
                index_elements=["movie_id", "user_id"],
                # Si hay conflicto, actualiza estos campos
                set_={
                    "rating": review_values["rating"],
                    "comment": review_values["comment"],
                    # (No actualizamos 'created_at', solo 'updated_at' si lo tienes)
                },
            )
        )

        # 3. Ejecutar atómicamente
        await session.execute(insert_stmt)

        logger.info(
            f"Reseña creada/actualizada para película {review_values['movie_id']} por usuario {review_values['user_id']}."
        )

    except Exception as e:
        logger.error(f"Error al crear/actualizar reseña: {e}")
        raise ValueError(f"Error al procesar reseña") from e


async def process_review_updated(session: AsyncSession, review_data: dict):
    """
    Actualiza una reseña existente de forma segura.
    """
    review_id = review_data.get("id")
    if not review_id:
        # Si no hay ID, intenta hacer un UPSERT usando la lógica de 'crear'
        # Esto maneja el caso de que un 'update' llegue antes que el 'create'
        logger.warning("Update sin ID, intentando 'crear' (UPSERT)...")
        await process_review_created(session, review_data)
        return

    # 1. Obtener la fila y BLOQUEARLA para evitar race conditions de "update"
    db_review = await session.get(Review, review_id, with_for_update=True)

    if not db_review:
        logger.warning(f"Reseña con ID {review_id} no encontrada. Creando (UPSERT)...")
        await process_review_created(session, review_data)
        return

    # 2. Actualizar campos (ahora es seguro, tenemos el bloqueo)
    if "rating" in review_data:
        db_review.rating = review_data["rating"]
    if "comment" in review_data:
        db_review.comment = review_data["comment"]

    session.add(db_review)
    logger.info(f" Reseña con ID {review_id} actualizada exitosamente.")


async def process_review_deleted(session: AsyncSession, review_data: dict):
    """
    Elimina una reseña de la base de datos. (Esto ya es seguro)
    """
    review_id = review_data.get("id")
    if not review_id:
        logger.error(" No se proporcionó un ID de reseña para eliminar.")
        raise ValueError("ID de reseña requerido para eliminación")

    # .get() es seguro.
    db_review = await session.get(Review, review_id)
    if not db_review:
        logger.warning(f"Reseña con ID {review_id} no encontrada para eliminar.")
        return

    # .delete() es seguro.
    await session.delete(db_review)
    logger.info(f" Reseña con ID {review_id} eliminada exitosamente.")