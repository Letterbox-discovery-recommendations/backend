from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import User
import logging
from datetime import datetime

# NUEVO: Importar 'insert' de PostgreSQL
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)


async def process_user_created(session: AsyncSession, user_data: dict):
    """
    Procesa la creación (o actualización) de un nuevo usuario de forma atómica (UPSERT).
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        # Validar campos requeridos
        required_fields = ["idUsuario", "nombre", "pais", "fechaRegistro"]
        for field in required_fields:
            if field not in user_data:
                raise ValueError(
                    f"Campo requerido '{field}' no encontrado en los datos de usuario"
                )

        # 1. Preparar los datos
        registration_date = (
            datetime.fromisoformat(user_data["fechaRegistro"]).date()
            if isinstance(user_data["fechaRegistro"], str)
            else user_data["fechaRegistro"]
        )

        user_values = {
            "id": user_data["idUsuario"],
            "name": user_data["nombre"],
            "country": user_data["pais"],
            "registration_date": registration_date,
        }

        # 2. Crear el statement 'INSERT ... ON CONFLICT DO UPDATE'
        insert_stmt = (
            insert(User)
            .values(**user_values)
            .on_conflict_do_update(
                index_elements=["id"],  # Conflicto detectado en la Primary Key 'id'
                set_={
                    # Si ya existe, actualiza estos campos
                    "name": user_values["name"],
                    "country": user_values["country"],
                    "registration_date": user_values["registration_date"],
                },
            )
        )

        # 3. Ejecutar atómicamente
        await session.execute(insert_stmt)

        logger.info(
            f"Usuario creado/actualizado (UPSERT): {user_values['name']} (ID: {user_values['id']})"
        )
    except Exception as e:
        logger.error(f"Error al procesar usuario (UPSERT): {e}")
        raise ValueError("Error al procesar usuario") from e


async def process_user_updated(session: AsyncSession, user_data: dict):
    """
    Procesa la actualización de un usuario existente de forma segura.
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        if "idUsuario" not in user_data:
            raise ValueError("Campo requerido 'idUsuario' no encontrado")

        user_id = user_data["idUsuario"]

        # 1. Obtener y BLOQUEAR la fila del usuario para evitar 'race conditions' de updates
        db_user = await session.get(User, user_id, with_for_update=True)

        if not db_user:
            logger.warning(
                f"Usuario {user_id} no encontrado para actualizar. Se intentará crear (UPSERT)..."
            )
            # Si no existe, delega a la función 'crear' (que es atómica)
            # Necesitamos asegurar que todos los campos requeridos estén presentes
            if not all(k in user_data for k in ["nombre", "pais", "fechaRegistro"]):
                logger.error(
                    f"Faltan datos para crear usuario {user_id} desde un evento 'update'"
                )
                raise ValueError(
                    "Datos insuficientes para crear usuario desde un 'update'"
                )

            await process_user_created(session, user_data)
            return

        # 2. Actualizar campos proporcionados (ahora es seguro, tenemos el bloqueo)
        if "nombre" in user_data:
            db_user.name = user_data["nombre"]
        if "pais" in user_data:
            db_user.country = user_data["pais"]
        if "fechaRegistro" in user_data:
            db_user.registration_date = (
                datetime.fromisoformat(user_data["fechaRegistro"]).date()
                if isinstance(user_data["fechaRegistro"], str)
                else user_data["fechaRegistro"]
            )

        session.add(db_user)  # SQLModel sabe que esto es un UPDATE
        logger.info(f"Usuario actualizado: {db_user.name} (ID: {db_user.id})")

    except Exception as e:
        logger.error(f"Error al actualizar usuario: {e}")
        raise ValueError("Error al actualizar usuario") from e