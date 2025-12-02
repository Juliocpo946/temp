import json
import threading
import pika
from datetime import datetime
from src.infrastructure.config.settings import (
    ACTIVITY_DETAILS_REQUEST_QUEUE,
    ACTIVITY_DETAILS_RESPONSE_QUEUE,
    LOG_SERVICE_QUEUE,
    AMQP_URL
)
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.activity_log_repository_impl import ActivityLogRepositoryImpl
from src.infrastructure.persistence.repositories.external_activity_repository_impl import ExternalActivityRepositoryImpl


class ActivityDetailsConsumer:
    def __init__(self, rabbitmq_client):
        self.rabbitmq_client = rabbitmq_client
        self._connection = None
        self._channel = None

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_requests, daemon=True)
        thread.start()
        print(f"[ACTIVITY_DETAILS_CONSUMER] [INFO] Consumer de solicitudes de detalles iniciado")

    def _consume_requests(self) -> None:
        while True:
            try:
                parameters = pika.URLParameters(AMQP_URL)
                parameters.heartbeat = 300
                parameters.blocked_connection_timeout = 150
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                
                self._channel.basic_qos(prefetch_count=10)
                self._channel.basic_consume(
                    queue=ACTIVITY_DETAILS_REQUEST_QUEUE,
                    on_message_callback=self._callback,
                    auto_ack=False
                )
                
                print(f"[RABBITMQ_CLIENT] [INFO] Escuchando en cola: {ACTIVITY_DETAILS_REQUEST_QUEUE}")
                self._channel.start_consuming()
            except Exception as e:
                print(f"[ACTIVITY_DETAILS_CONSUMER] [ERROR] Error en consumer: {str(e)}")
                import time
                time.sleep(5)

    def _callback(self, ch, method, properties, body) -> None:
        db = SessionLocal()
        try:
            message = json.loads(body)
            activity_uuid = message.get("activity_uuid")
            correlation_id = message.get("correlation_id")
            reply_to = message.get("reply_to")

            print(f"[ACTIVITY_DETAILS_CONSUMER] [INFO] Solicitud recibida para actividad: {activity_uuid}")

            activity_log_repo = ActivityLogRepositoryImpl(db)
            external_activity_repo = ExternalActivityRepositoryImpl(db)

            activity_log = activity_log_repo.get_by_uuid(activity_uuid)
            
            if not activity_log:
                print(f"[ACTIVITY_DETAILS_CONSUMER] [ERROR] Actividad no encontrada: {activity_uuid}")
                self._send_error_response(correlation_id, activity_uuid, reply_to)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            external_activity = external_activity_repo.get_by_external_id(
                activity_log.external_activity_id
            )

            if not external_activity:
                print(f"[ACTIVITY_DETAILS_CONSUMER] [ERROR] Actividad externa no encontrada: {activity_log.external_activity_id}")
                self._send_error_response(correlation_id, activity_uuid, reply_to)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            response = {
                "type": "activity_details_response",
                "activity_uuid": activity_uuid,
                "title": external_activity.title,
                "subtitle": external_activity.subtitle,
                "content": external_activity.content,
                "activity_type": external_activity.activity_type,
                "correlation_id": correlation_id
            }

            target_queue = reply_to if reply_to else ACTIVITY_DETAILS_RESPONSE_QUEUE
            success = self.rabbitmq_client.publish(target_queue, response, correlation_id=correlation_id)

            if success:
                print(f"[ACTIVITY_DETAILS_CONSUMER] [INFO] Respuesta enviada para actividad: {activity_uuid}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[ACTIVITY_DETAILS_CONSUMER] [ERROR] Error procesando solicitud: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    def _send_error_response(self, correlation_id: str, activity_uuid: str, reply_to: str = None) -> None:
        error_response = {
            "type": "activity_details_response",
            "activity_uuid": activity_uuid,
            "error": "Activity not found",
            "correlation_id": correlation_id
        }
        target_queue = reply_to if reply_to else ACTIVITY_DETAILS_RESPONSE_QUEUE
        self.rabbitmq_client.publish(target_queue, error_response, correlation_id=correlation_id)