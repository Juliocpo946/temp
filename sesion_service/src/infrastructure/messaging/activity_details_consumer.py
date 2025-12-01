import json
import threading
from datetime import datetime
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import ACTIVITY_DETAILS_REQUEST_QUEUE, ACTIVITY_DETAILS_RESPONSE_QUEUE, LOG_SERVICE_QUEUE
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.activity_log_repository_impl import ActivityLogRepositoryImpl
from src.infrastructure.persistence.repositories.external_activity_repository_impl import ExternalActivityRepositoryImpl


class ActivityDetailsConsumer:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.rabbitmq_client = rabbitmq_client

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_requests, daemon=True)
        thread.start()
        print(f"[ACTIVITY_DETAILS_CONSUMER] [INFO] Consumer de solicitudes de detalles iniciado")

    def _consume_requests(self) -> None:
        self.rabbitmq_client.consume(ACTIVITY_DETAILS_REQUEST_QUEUE, self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        db = SessionLocal()
        try:
            message = json.loads(body)
            activity_uuid = message.get("activity_uuid")
            correlation_id = message.get("correlation_id")

            print(f"[ACTIVITY_DETAILS_CONSUMER] [INFO] Solicitud recibida para actividad: {activity_uuid}")

            activity_log_repo = ActivityLogRepositoryImpl(db)
            external_activity_repo = ExternalActivityRepositoryImpl(db)

            activity_log = activity_log_repo.get_by_uuid(activity_uuid)
            
            if not activity_log:
                print(f"[ACTIVITY_DETAILS_CONSUMER] [ERROR] Actividad no encontrada: {activity_uuid}")
                self._send_error_response(correlation_id, activity_uuid)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            external_activity = external_activity_repo.get_by_external_id(
                activity_log.external_activity_id
            )

            if not external_activity:
                print(f"[ACTIVITY_DETAILS_CONSUMER] [ERROR] Actividad externa no encontrada: {activity_log.external_activity_id}")
                self._send_error_response(correlation_id, activity_uuid)
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

            success = self.rabbitmq_client.publish(ACTIVITY_DETAILS_RESPONSE_QUEUE, response)
            
            if success:
                print(f"[ACTIVITY_DETAILS_CONSUMER] [INFO] Respuesta enviada para actividad: {activity_uuid}")
            else:
                print(f"[ACTIVITY_DETAILS_CONSUMER] [ERROR] Error enviando respuesta para actividad: {activity_uuid}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[ACTIVITY_DETAILS_CONSUMER] [ERROR] Error procesando solicitud: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    def _send_error_response(self, correlation_id: str, activity_uuid: str) -> None:
        response = {
            "type": "activity_details_response",
            "activity_uuid": activity_uuid,
            "title": None,
            "subtitle": None,
            "content": None,
            "activity_type": None,
            "correlation_id": correlation_id,
            "error": "Activity not found"
        }
        self.rabbitmq_client.publish(ACTIVITY_DETAILS_RESPONSE_QUEUE, response)

    def _publish_log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "session-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)