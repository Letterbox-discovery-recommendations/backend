import pika
import json
from dotenv import load_dotenv
from sqlalchemy import Engine
from sqlmodel import Session
from app.db.utils import get_engine
from app.db.movie_utils import process_movie_data, update_movie_data, delete_movie_data
from app.db.review_utils import process_review_created, process_review_updated, process_review_deleted
from app.db.social_utils import process_follow_created, process_follow_deleted
import os
import logging

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self):
        load_dotenv()
        self.engine: Engine = get_engine()

        rabbitmq_url = os.getenv("RABBIT_MQ_URL")
        params = pika.URLParameters(rabbitmq_url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        logger.info("Conexión con RabbitMQ establecida.")

        self.routing_key_handlers = {
            "peliculas.pelicula.creada": self.handle_movie_created,
            "peliculas.pelicula.actualizada": self.handle_movie_updated,
            "peliculas.pelicula.borrada": self.handle_movie_deleted,
            "resenas.resena.creada": self.handle_review_created,
            "resenas.resena.actualizada": self.handle_review_updated,
            "resenas.resena.eliminada": self.handle_review_deleted,
            "social.seguimiento.creado": self.handle_follow_created,
            "social.seguimiento.borrado": self.handle_follow_deleted
        }


    def handle_movie_created(self, session, body_data):
        logger.info(f"Procesando creación de película: '{body_data.get('titulo', 'N/A')}'")
        process_movie_data(session, body_data)
        logger.info("Película creada exitosamente.")

    def handle_movie_updated(self, session, body_data):
        logger.info(f"Procesando actualización de película: '{body_data.get('titulo', 'N/A')}'")
        update_movie_data(session, body_data)
        logger.info("Película actualizada exitosamente.")

    def handle_movie_deleted(self, session, body_data):
        movie_id = body_data.get('id', 'N/A')
        logger.info(f"Procesando eliminación de película ID: {movie_id}")
        delete_movie_data(session, body_data)
        logger.info("Película eliminada exitosamente.")

    def handle_review_created(self, session, body_data):
        logger.info(f"Procesando creación de reseña para película ID: {body_data.get('movie_id', 'N/A')}")
        process_review_created(session, body_data)
        logger.info("Reseña creada exitosamente.")

    def handle_review_updated(self, session, body_data):
        logger.info(f"Procesando actualización de reseña ID: {body_data.get('id', 'N/A')}")
        process_review_updated(session, body_data)
        logger.info("Reseña actualizada exitosamente.")

    def handle_review_deleted(self, session, body_data):
        logger.info(f"Procesando eliminación de reseña ID: {body_data.get('id', 'N/A')}")
        process_review_deleted(session, body_data)
        logger.info("Reseña eliminada exitosamente.")

    def handle_follow_created(self, session, body_data):
        follower = body_data.get('follower_id', 'N/A')
        followed = body_data.get('followed_id', 'N/A')
        logger.info(f"Procesando nuevo seguimiento: usuario {follower} sigue a {followed}")
        process_follow_created(session, body_data)
        logger.info("Relación de seguimiento creada exitosamente.")

    def handle_follow_deleted(self, session, body_data):
        follower = body_data.get('follower_id', 'N/A')
        followed = body_data.get('followed_id', 'N/A')
        logger.info(f"Procesando eliminación de seguimiento: usuario {follower} deja de seguir a {followed}")
        process_follow_deleted(session, body_data)
        logger.info("Relación de seguimiento eliminada exitosamente.")




    def generic_event_callback(self, ch, method, properties, body):
        routing_key = method.routing_key
        delivery_tag = method.delivery_tag

        logger.info(
            f"[MENSAJE RECIBIDO] Routing Key: '{routing_key}', Delivery Tag: {delivery_tag}"
        )
        handler = self.routing_key_handlers.get(routing_key)

        if not handler:
            logger.warning(
                f"No se encontró un manejador para la routing key '{routing_key}'. Descartando mensaje."
            )
            ch.basic_ack(delivery_tag=delivery_tag)
            return

        try:
            body_data = json.loads(body.decode("utf-8"))
            logger.info(body_data)

            with Session(self.engine) as session:
                handler(session, body_data["data"])
                session.commit()

            ch.basic_ack(delivery_tag=delivery_tag)
            logger.info(
                f"Mensaje con routing key '{routing_key}' procesado y confirmado (ACK)."
            )

        except json.JSONDecodeError as e:
            logger.error(f"Error de formato JSON: {e}. El mensaje no es válido. Descartando.")
            ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
        except Exception as e:
            logger.error(
                f"Error inesperado procesando mensaje con routing key '{routing_key}': {e}"
            )
            ch.basic_nack(delivery_tag=delivery_tag, requeue=False)

    def run(self, queue_name: str):

        logger.info(f"\nConfigurando consumidor para la cola '{queue_name}'...")


        self.channel.queue_declare(queue=queue_name, durable=True)

        self.channel.basic_consume(
            queue=queue_name, on_message_callback=self.generic_event_callback
        )

        try:
            logger.info(f"Esperando mensajes en '{queue_name}'. Para salir presiona CTRL+C")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Cerrando conexión...")
            self.connection.close()
            logger.info("Conexión cerrada.")


def start_consuming():
    MY_SERVICE_QUEUE = "core.recommendations.queue"

    consumer = RabbitMQConsumer()
    consumer.run(MY_SERVICE_QUEUE)

# Para ejecutar el consumidor
if __name__ == "__main__":
    start_consuming()
