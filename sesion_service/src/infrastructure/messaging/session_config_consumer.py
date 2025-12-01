import json
import threading
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import (
    SESSION_CONFIG_REQUEST_QUEUE,
    SESSION_CONFIG_RESPONSE_QUEUE,
    LOG_SERVICE_QUEUE
)
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.analysis_config_repository_impl import AnalysisConfigRepositoryImpl


class SessionConfigConsumer:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.rabbitmq_client = rabbitmq_client

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_requests, daemon=True)
        thread.start()
        print(f"[SESSION_CONFIG_CONSUMER] [INFO] Consumer de solicitudes de configuracion iniciado")

    def _consume_requests(self) -> None:
        self.rabbitmq_client.consume(SESSION_CONFIG_REQUEST_QUEUE, self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        db = SessionLocal()
        try:
            message = json.loads(body)
            session_id = message.get("session_id")
            correlation_id = message.get("correlation_id")

            print(f"[SESSION_CONFIG_CONSUMER] [INFO] Solicitud de config recibida para sesion: {session_id}")

            config_repo = AnalysisConfigRepositoryImpl(db)
            config = config_repo.get_by_session_id(session_id)

            if config:
                response = {
                    "type": "session_config_response",
                    "session_id": session_id,
                    "correlation_id": correlation_id,
                    "cognitive_analysis_enabled": config.cognitive_analysis_enabled,
                    "text_notifications": config.text_notifications,
                    "video_suggestions": config.video_suggestions,
                    "vibration_alerts": config.vibration_alerts,
                    "pause_suggestions": config.pause_suggestions
                }
            else:
                response = {
                    "type": "session_config_response",
                    "session_id": session_id,
                    "correlation_id": correlation_id,
                    "cognitive_analysis_enabled": True,
                    "text_notifications": True,
                    "video_suggestions": True,
                    "vibration_alerts": True,
                    "pause_suggestions": True,
                    "is_default": True
                }

            success = self.rabbitmq_client.publish(SESSION_CONFIG_RESPONSE_QUEUE, response)

            if success:
                print(f"[SESSION_CONFIG_CONSUMER] [INFO] Respuesta de config enviada para sesion: {session_id}")
            else:
                print(f"[SESSION_CONFIG_CONSUMER] [ERROR] Error enviando respuesta de config")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[SESSION_CONFIG_CONSUMER] [ERROR] Error procesando solicitud: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    def _publish_log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "session-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)