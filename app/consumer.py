import asyncio
import json
import logging
import os
from dotenv import load_dotenv
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from sqlmodel.ext.asyncio.session import AsyncSession

# Importamos el engine y la fábrica de sesiones ASYNC de tu nuevo db/utils
from app.db.utils import engine, AsyncSessionLocal
from app.models import Mensaje

# IMPORTANTE: Todas estas funciones deben ser actualizadas a 'async def'
# y deben usar métodos asíncronos (await session.exec(), etc.)
from app.db.movie_utils import process_movie_data, update_movie_data, delete_movie_data
from app.db.review_utils import (
    process_review_created,
    process_review_updated,
    process_review_deleted,
)
from app.db.social_utils import process_follow_created, process_follow_deleted
from app.db.user_utils import process_user_created, process_user_updated

load_dotenv()
logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBIT_MQ_URL")
        self.routing_key_handlers = {
            "peliculas.pelicula.creada": self.handle_movie_created,
            "peliculas.pelicula.actualizada": self.handle_movie_updated,
            "peliculas.pelicula.borrada": self.handle_movie_deleted,
            "resenas.resena.creada": self.handle_review_created,
            "resenas.resena.actualizada": self.handle_review_updated,
            "resenas.resena.eliminada": self.handle_review_deleted,
            "social.seguimiento.creado": self.handle_follow_created,
            "social.seguimiento.borrado": self.handle_follow_deleted,
            "usuarios.usuario.creado": self.handle_user_created,
            "usuarios.usuario.actualizado": self.handle_user_updated,
        }

    async def handle_movie_created(self, session: AsyncSession, body_data):
        logger.info(
            f"Procesando creación de película: '{body_data.get('titulo', 'N/A')}'"
        )
        await process_movie_data(
            session, body_data
        )
        logger.info("Película creada exitosamente.")

    async def handle_movie_updated(self, session: AsyncSession, body_data):
        logger.info(
            f"Procesando actualización de película: '{body_data.get('titulo', 'N/A')}'"
        )
        await update_movie_data(
            session, body_data
        )  # Idealmente: await update_movie_data(...)
        logger.info("Película actualizada exitosamente.")

    async def handle_movie_deleted(self, session: AsyncSession, body_data):
        movie_id = body_data.get("id", "N/A")
        logger.info(f"Procesando eliminación de película ID: {movie_id}")
        await delete_movie_data(session, body_data)
        logger.info("Película eliminada exitosamente.")

    # ... (Repite el patrón 'async def' para el resto de handlers) ...
    async def handle_review_created(self, session: AsyncSession, body_data):
        await process_review_created(session, body_data)

    async def handle_review_updated(self, session: AsyncSession, body_data):
        await process_review_updated(session, body_data)

    async def handle_review_deleted(self, session: AsyncSession, body_data):
        await process_review_deleted(session, body_data)

    async def handle_follow_created(self, session: AsyncSession, body_data):
        await process_follow_created(session, body_data)

    async def handle_follow_deleted(self, session: AsyncSession, body_data):
        await process_follow_deleted(session, body_data)

    async def handle_user_created(self, session: AsyncSession, body_data):
        await process_user_created(session, body_data)

    async def handle_user_updated(self, session: AsyncSession, body_data):
        await process_user_updated(session, body_data)

    async def on_message(self, message: AbstractIncomingMessage):
        """
        Callback principal asíncrono para cada mensaje recibido.
        """
        routing_key = message.routing_key
        logger.info(
            f"[MENSAJE RECIBIDO] Routing Key: '{routing_key}', ID: {message.message_id}"
        )

        handler = self.routing_key_handlers.get(routing_key)

        if not handler:
            logger.warning(f"No se encontró handler para '{routing_key}'. Descartando.")
            await message.ack()
            return

        async with message.process(ignore_processed=True):
            # 1. Validar JSON
            try:
                body_data = json.loads(message.body.decode("utf-8"))
                # logger.debug(body_data) # Reduce el ruido en producción
            except json.JSONDecodeError as e:
                logger.error(f"Error JSON: {e}. Descartando mensaje.")
                return

                # 2. Transacción de Auditoría (Log)
            try:
                async with AsyncSessionLocal() as session_log:
                    mensaje_log = Mensaje(
                        evento=routing_key,
                        tipo="CONSUME",
                        data=body_data,
                    )
                    session_log.add(mensaje_log)
                    await session_log.commit()
                logger.info("Log de auditoría guardado (async).")
            except Exception as e:
                logger.critical(f"Fallo CRÍTICO al guardar log de auditoría: {e}")

                raise e


            try:
                async with AsyncSessionLocal() as session_data:
                    # Llamamos al handler (que ahora debe ser async)
                    if asyncio.iscoroutinefunction(handler):
                        await handler(session_data, body_data["data"])
                    else:
                        logger.warning(
                            f"⚠️ Ejecutando handler SINCRONO para {routing_key}. Actualízalo a 'async def'."
                        )
                        handler(session_data, body_data["data"])

                    await session_data.commit()

                logger.info(f"Mensaje '{routing_key}' procesado exitosamente.")

            except Exception as e:
                logger.error(f"Error al PROCESAR mensaje '{routing_key}': {e}")
                # Lanzar la excepción dentro de 'message.process' provocará un NACK.
                # Si quieres que NO se reencole, deberías capturarla y hacer message.reject(requeue=False)
                raise e

    async def run(self, queue_name: str):
        logger.info("Conectando a RabbitMQ (Async)...")
        connection = await aio_pika.connect_robust(self.rabbitmq_url)

        async with connection:
            channel = await connection.channel()
            # Declara la cola (durable=True para persistencia)


            await channel.set_qos(prefetch_count=8)


            queue = await channel.declare_queue(queue_name, durable=True)

            logger.info(f"✅ Consumidor esperando mensajes en '{queue_name}'")

            # Procesa mensajes concurrentemente
            await queue.consume(self.on_message)

            # Mantiene el consumidor corriendo para siempre
            await asyncio.Future()


# Función de entrada para lifespan
async def start_consuming():
    MY_SERVICE_QUEUE = "core.recommendations.queue"
    consumer = RabbitMQConsumer()
    try:
        await consumer.run(MY_SERVICE_QUEUE)
    except asyncio.CancelledError:
        logger.info("Tarea del consumidor cancelada. Apagando limpiamente.")

if __name__ == "__main__":
    # Para probarlo aisladamente
    asyncio.run(start_consuming())