from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Follow
import logging

# NUEVO: Importar 'insert' de PostgreSQL
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)


async def process_follow_created(session: AsyncSession, follow_data: dict):
    """
    Procesa la creación de una nueva relación de seguimiento de forma atómica.
    Usa 'INSERT ... ON CONFLICT DO NOTHING' para ser idempotente.
    """
    try:
        # Validar campos requeridos
        required_fields = ["follower_id", "followed_id"]
        for field in required_fields:
            if field not in follow_data:
                raise ValueError(f"Campo requerido '{field}' no encontrado")



        # 1. Preparar los datos
        follow_values = {
            "follower_id": str(follow_data["follower_id"]),
            "followed_id": str(follow_data["followed_id"]),
        }

        # 2. Crear el statement 'INSERT ... ON CONFLICT'
        insert_stmt = (
            insert(Follow)
            .values(**follow_values)
            .on_conflict_do_nothing(
                # Asume que tu 'UNIQUE constraint' es en estas dos columnas
                index_elements=["follower_id", "followed_id"]
            )
        )

        # 3. Ejecutar atómicamente
        await session.execute(insert_stmt)

        logger.info(
            f"Relación de seguimiento procesada (atómicamente): "
            f"usuario {follow_values['follower_id']} sigue a {follow_values['followed_id']}."
        )
    except Exception as e:
        logger.error(f"Error al procesar relación de seguimiento: {e}")
        raise ValueError("Error al procesar seguimiento") from e


# (process_follow_deleted no necesita cambios, ya es seguro)
async def process_follow_deleted(session: AsyncSession, follow_data: dict):
    """
    Elimina una relación de seguimiento. (Async)
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        db_follow = None
        if "follower_id" in follow_data and "unfollowed_id" in follow_data:
            follow_result = await session.exec(
                select(Follow).where(
                    Follow.follower_id == follow_data["follower_id"],
                    Follow.followed_id == follow_data["unfollowed_id"],
                )
            )
            db_follow = follow_result.first()
        elif "id" in follow_data:
            db_follow = await session.get(Follow, follow_data["id"])
        else:
            logger.error(
                "No se proporcionaron datos suficientes para eliminar el seguimiento."
            )
            raise ValueError(
                "Se requiere 'id' o 'follower_id' y 'unfollowed_id' para eliminación"
            )

        if not db_follow:
            logger.warning(
                f"Relación de seguimiento no encontrada para eliminar: "
                f"{follow_data.get('follower_id')} -> {follow_data.get('followed_id')}"
            )
            return

        follower_id = db_follow.follower_id
        followed_id = db_follow.followed_id

        await session.delete(db_follow)
        logger.info(
            f"Relación de seguimiento eliminada: usuario {follower_id} "
            f"dejó de seguir a usuario {followed_id}."
        )
    except Exception as e:
        logger.error(f"Error al eliminar relación de seguimiento: {e}")
        raise ValueError(f"Error al eliminar seguimiento") from e