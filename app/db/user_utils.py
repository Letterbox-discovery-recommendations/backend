from sqlmodel import Session, select
from app.models import User
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def process_user_created(session: Session, user_data: dict):
    """
    Procesa la creación de un nuevo usuario.
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        # Validar campos requeridos
        required_fields = ["idUsuario", "nombre", "pais", "fechaRegistro"]
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Campo requerido '{field}' no encontrado en los datos de usuario")

        # Verificar que no exista ya el usuario
        existing_user = session.exec(
            select(User).where(User.id == user_data["idUsuario"])
        ).first()

        if existing_user:
            logger.warning(
                f"El usuario {user_data['idUsuario']} ya existe. Actualizando datos..."
            )
            # Actualizar campos existentes
            existing_user.name = user_data["nombre"]
            existing_user.country = user_data["pais"]
            # Convertir fechaRegistro string a date si es necesario
            if isinstance(user_data["fechaRegistro"], str):
                existing_user.registration_date = datetime.fromisoformat(user_data["fechaRegistro"]).date()
            else:
                existing_user.registration_date = user_data["fechaRegistro"]
            return

        # Crear el usuario
        db_user = User(
            id=user_data["idUsuario"],
            name=user_data["nombre"],
            country=user_data["pais"],
            registration_date=datetime.fromisoformat(user_data["fechaRegistro"]).date() if isinstance(user_data["fechaRegistro"], str) else user_data["fechaRegistro"]
        )
        session.add(db_user)
        logger.info(
            f"Usuario creado: {db_user.name} (ID: {db_user.id})"
        )
    except Exception as e:
        logger.error(f"Error al crear usuario: {e}")
        raise ValueError(f"Error al procesar usuario") from e


def process_user_updated(session: Session, user_data: dict):
    """
    Procesa la actualización de un usuario existente.
    IMPORTANTE: Esta función NO hace commit. El commit se debe manejar fuera.
    """
    try:
        # Validar campo requerido
        if "idUsuario" not in user_data:
            raise ValueError("Campo requerido 'idUsuario' no encontrado")

        # Buscar usuario existente
        db_user = session.exec(
            select(User).where(User.id == user_data["idUsuario"])
        ).first()

        if not db_user:
            logger.warning(
                f"Usuario {user_data['idUsuario']} no encontrado. Creando nuevo usuario..."
            )
            # Si no existe, crear como nuevo
            process_user_created(session, user_data)
            return

        # Actualizar campos proporcionados
        if "nombre" in user_data:
            db_user.name = user_data["nombre"]
        if "pais" in user_data:
            db_user.country = user_data["pais"]
        if "fechaRegistro" in user_data:
            db_user.registration_date = datetime.fromisoformat(user_data["fechaRegistro"]).date() if isinstance(user_data["fechaRegistro"], str) else user_data["fechaRegistro"]

        logger.info(
            f"Usuario actualizado: {db_user.name} (ID: {db_user.id})"
        )
    except Exception as e:
        logger.error(f"Error al actualizar usuario: {e}")
        raise ValueError(f"Error al actualizar usuario") from e