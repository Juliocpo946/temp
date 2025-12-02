import json
import threading
import pika
from src.infrastructure.config.settings import (
    MONITORING_WEBSOCKET_EVENTS_QUEUE,
    LOG_SERVICE_QUEUE,
    AMQP_URL
)
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.activity_log_repository_impl import ActivityLogRepositoryImpl

class WebsocketEventConsumer:
    def __init__(self):
        self._connection = None
        self._channel = None

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_events, daemon=True)
        thread.start()

    def _consume_events(self) -> None:
        while True:
            try:
                parameters = pika.URLParameters(AMQP_URL)
                parameters.heartbeat = 300
                parameters.blocked_connection_timeout = 150
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                
                self._channel.basic_qos(prefetch_count=10)
                self._channel.basic_consume(
                    queue=MONITORING_WEBSOCKET_EVENTS_QUEUE,
                    on_message_callback=self._callback,
                    auto_ack=False
                )
                
                print(f"[RABBITMQ_CLIENT] [INFO] Escuchando en cola: {MONITORING_WEBSOCKET_EVENTS_QUEUE}")
                self._channel.start_consuming()
            except Exception as e:
                print(f"[WEBSOCKET_EVENT_CONSUMER] [ERROR] Error en consumer: {str(e)}")
                import time
                time.sleep(5)

    def _callback(self, ch, method, properties, body) -> None:
        db = SessionLocal()
        try:
            message = json.loads(body)
            event_type = message.get("type")

            if event_type == "websocket_disconnected":
                self._handle_websocket_disconnected(db, message)

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[WEBSOCKET_EVENT_CONSUMER] [ERROR] Error procesando evento: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    def _handle_websocket_disconnected(self, db, message: dict) -> None:
        activity_uuid = message.get("activity_uuid")
        session_id = message.get("session_id")
        reason = message.get("reason", "unknown")

        if not activity_uuid:
            print(f"[WEBSOCKET_EVENT_CONSUMER] [ERROR] Evento websocket_disconnected sin activity_uuid")
            return

        activity_repo = ActivityLogRepositoryImpl(db)
        activity = activity_repo.get_by_uuid(activity_uuid)

        if not activity:
            print(f"[WEBSOCKET_EVENT_CONSUMER] [ERROR] Actividad no encontrada: {activity_uuid}")
            return

        if activity.status == "en_progreso":
            activity.abandon()
            activity_repo.update(activity)
            print(f"[WEBSOCKET_EVENT_CONSUMER] [INFO] Actividad {activity_uuid} marcada como abandonada")
        elif activity.status == "pausada":
            print(f"[WEBSOCKET_EVENT_CONSUMER] [INFO] Actividad {activity_uuid} ya pausada")
        else:
            print(f"[WEBSOCKET_EVENT_CONSUMER] [INFO] Actividad {activity_uuid} estado {activity.status}")