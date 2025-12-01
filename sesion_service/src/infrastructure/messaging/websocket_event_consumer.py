import json
import threading
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import MONITORING_WEBSOCKET_EVENTS_QUEUE, LOG_SERVICE_QUEUE
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.activity_log_repository_impl import ActivityLogRepositoryImpl

class WebsocketEventConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_events, daemon=True)
        thread.start()

    def _consume_events(self) -> None:
        self.rabbitmq_client.consume(MONITORING_WEBSOCKET_EVENTS_QUEUE, self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        db = SessionLocal()
        try:
            message = json.loads(body)
            event_type = message.get("type")

            if event_type == "websocket_disconnected":
                self._handle_websocket_disconnected(db, message)

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self._log(f"Error procesando evento de websocket: {str(e)}", "error")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    def _handle_websocket_disconnected(self, db, message: dict) -> None:
        activity_uuid = message.get("activity_uuid")
        session_id = message.get("session_id")
        reason = message.get("reason", "unknown")

        if not activity_uuid:
            self._log("Evento websocket_disconnected sin activity_uuid", "error")
            return

        activity_repo = ActivityLogRepositoryImpl(db)
        activity = activity_repo.get_by_uuid(activity_uuid)

        if not activity:
            self._log(f"Actividad no encontrada: {activity_uuid}", "error")
            return

        if activity.status == "en_progreso":
            activity.abandon()
            activity_repo.update(activity)
            self._log(f"Actividad {activity_uuid} marcada como abandonada por desconexion de WebSocket")
        elif activity.status == "pausada":
            self._log(f"Actividad {activity_uuid} ya estaba pausada, se mantiene igual")
        else:
            self._log(f"Actividad {activity_uuid} tiene estado {activity.status}, no se modifica")

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "session-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)