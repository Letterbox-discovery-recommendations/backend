from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession  # NUEVO: AsyncSession
from app.models import Follow
import logging

logger = logging.getLogger(__name__)


# NUEVO: 'async def' y 'AsyncSession'
async def process_follow_created(session: AsyncSession, follow_data: dict):
    """
    Procesa la creación de una nueva relación de seguimiento. (Async)
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        # Validar campos requeridos
        required_fields = ["follower_id", "followed_id"]
        for field in required_fields:
            if field not in follow_data:
                raise ValueError(f"Campo requerido '{field}' no encontrado en los datos de seguimiento")

        # Verificar que no exista ya la relación
        # NUEVO: 'await' y paréntesis en session.exec()
        existing_follow_result = await session.exec(
            select(Follow).where(
                Follow.follower_id == follow_data["follower_id"],
                Follow.followed_id == follow_data["followed_id"]
            )
        )
        existing_follow = existing_follow_result.first()

        if existing_follow:
            logger.warning(
                f"La relación de seguimiento ya existe: usuario {follow_data['follower_id']} "
                f"sigue a usuario {follow_data['followed_id']}."
            )
            return

        # Crear la relación de seguimiento
        db_follow = Follow(
            follower_id=follow_data["follower_id"],
            followed_id=follow_data["followed_id"]
        )
        session.add(db_follow)  # .add() no es async
        logger.info(
            f"Relación de seguimiento creada: usuario {db_follow.follower_id} "
            f"ahora sigue a usuario {db_follow.followed_id}."
        )
    except Exception as e:
        logger.error(f"Error al crear relación de seguimiento: {e}")
        raise ValueError(f"Error al procesar seguimiento") from e


# NUEVO: 'async def' y 'AsyncSession'
async def process_follow_deleted(session: AsyncSession, follow_data: dict):
    """
    Elimina una relación de seguimiento. (Async)
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        db_follow = None
        # Buscar por follower_id y followed_id
        if "follower_id" in follow_data and "followed_id" in follow_data:
            # NUEVO: 'await' y paréntesis en session.exec()
            follow_result = await session.exec(
                select(Follow).where(
                    Follow.follower_id == follow_data["follower_id"],
                    Follow.followed_id == follow_data["followed_id"]
                )
            )
            db_follow = follow_result.first()
        # O buscar por ID directo
        elif "id" in follow_data:
            # NUEVO: 'await' para session.get()
            db_follow = await session.get(Follow, follow_data["id"])
        else:
            logger.error("No se proporcionaron datos suficientes para eliminar el seguimiento.")
            raise ValueError("Se requiere 'id' o 'follower_id' y 'followed_id' para eliminación")

        if not db_follow:
            logger.warning(
                f"Relación de seguimiento no encontrada para eliminar: "
                f"{follow_data.get('follower_id')} -> {follow_data.get('followed_id')}"
            )
            return

        follower_id = db_follow.follower_id
        followed_id = db_follow.followed_id

        # NUEVO: 'await' para session.delete()
        await session.delete(db_follow)
        logger.info(
            f"Relación de seguimiento eliminada: usuario {follower_id} "
            f"dejó de seguir a usuario {followed_id}."
        )
    except Exception as e:
        logger.error(f"Error al eliminar relación de seguimiento: {e}")
        raise ValueError(f"Error al eliminar seguimiento") from e