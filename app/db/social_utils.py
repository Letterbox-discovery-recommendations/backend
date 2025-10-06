from sqlmodel import Session, select
from app.models import Follow
import logging

logger = logging.getLogger(__name__)


def process_follow_created(session: Session, follow_data: dict):
    """
    Procesa la creación de una nueva relación de seguimiento.
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        # Validar campos requeridos
        required_fields = ["follower_id", "followed_id"]
        for field in required_fields:
            if field not in follow_data:
                raise ValueError(f"Campo requerido '{field}' no encontrado en los datos de seguimiento")

        # Verificar que no exista ya la relación
        existing_follow = session.exec(
            select(Follow).where(
                Follow.follower_id == follow_data["follower_id"],
                Follow.followed_id == follow_data["followed_id"]
            )
        ).first()

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
        session.add(db_follow)
        logger.info(
            f"Relación de seguimiento creada: usuario {db_follow.follower_id} "
            f"ahora sigue a usuario {db_follow.followed_id}."
        )
    except Exception as e:
        logger.error(f"Error al crear relación de seguimiento: {e}")
        raise ValueError(f"Error al procesar seguimiento") from e


def process_follow_deleted(session: Session, follow_data: dict):
    """
    Elimina una relación de seguimiento.
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        # Buscar por follower_id y followed_id
        if "follower_id" in follow_data and "followed_id" in follow_data:
            db_follow = session.exec(
                select(Follow).where(
                    Follow.follower_id == follow_data["follower_id"],
                    Follow.followed_id == follow_data["followed_id"]
                )
            ).first()
        # O buscar por ID directo
        elif "id" in follow_data:
            db_follow = session.get(Follow, follow_data["id"])
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

        session.delete(db_follow)
        logger.info(
            f"Relación de seguimiento eliminada: usuario {follower_id} "
            f"dejó de seguir a usuario {followed_id}."
        )
    except Exception as e:
        logger.error(f"Error al eliminar relación de seguimiento: {e}")
        raise ValueError(f"Error al eliminar seguimiento") from e
