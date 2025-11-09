from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession  # NUEVO: AsyncSession
from app.models import User
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# NUEVO: 'async def' y 'AsyncSession'
async def process_user_created(session: AsyncSession, user_data: dict):
    """
    Procesa la creación de un nuevo usuario. (Async)
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

        # Verificar que no exista ya el usuario
        # NUEVO: 'await' y paréntesis en session.exec()
        existing_user_result = await session.exec(
            select(User).where(User.id == user_data["idUsuario"])
        )
        existing_user = existing_user_result.first()

        if existing_user:
            logger.warning(
                f"El usuario {user_data['idUsuario']} ya existe. Actualizando datos..."
            )
            # Actualizar campos existentes (esto no es I/O)
            existing_user.name = user_data["nombre"]
            existing_user.country = user_data["pais"]
            if isinstance(user_data["fechaRegistro"], str):
                existing_user.registration_date = datetime.fromisoformat(
                    user_data["fechaRegistro"]
                ).date()
            else:
                existing_user.registration_date = user_data["fechaRegistro"]

            session.add(existing_user)  # Añadir para que el commit lo guarde
            return

        # Crear el usuario
        db_user = User(
            id=user_data["idUsuario"],
            name=user_data["nombre"],
            country=user_data["pais"],
            registration_date=datetime.fromisoformat(user_data["fechaRegistro"]).date()
            if isinstance(user_data["fechaRegistro"], str)
            else user_data["fechaRegistro"],
        )
        session.add(db_user)  # .add() no es async
        logger.info(f"Usuario creado: {db_user.name} (ID: {db_user.id})")
    except Exception as e:
        logger.error(f"Error al crear usuario: {e}")
        raise ValueError(f"Error al procesar usuario") from e


# NUEVO: 'async def' y 'AsyncSession'
async def process_user_updated(session: AsyncSession, user_data: dict):
    """
    Procesa la actualización de un usuario existente. (Async)
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        # Validar campo requerido
        if "idUsuario" not in user_data:
            raise ValueError("Campo requerido 'idUsuario' no encontrado")

        # Buscar usuario existente
        # NUEVO: 'await' y paréntesis en session.exec()
        user_result = await session.exec(
            select(User).where(User.id == user_data["idUsuario"])
        )
        db_user = user_result.first()

        if not db_user:
            logger.warning(
                f"Usuario {user_data['idUsuario']} no encontrado. Creando nuevo usuario..."
            )
            # Si no existe, crear como nuevo
            # NUEVO: 'await' en la llamada recursiva
            await process_user_created(session, user_data)
            return

        # Actualizar campos proporcionados (esto no es I/O)
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

        session.add(db_user)  # Añadir para que el commit lo guarde
        logger.info(f"Usuario actualizado: {db_user.name} (ID: {db_user.id})")
    except Exception as e:
        logger.error(f"Error al actualizar usuario: {e}")
        raise ValueError(f"Error al actualizar usuario") from e