from datetime import datetime
from typing import Dict, Any
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import MONITORING_WEBSOCKET_EVENTS_QUEUE, LOG_SERVICE_QUEUE

class WebsocketEventPublisher:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.rabbitmq_client = rabbitmq_client

    def publish_websocket_disconnected(
        self,
        activity_uuid: str,
        session_id: str,
        reason: str = "connection_closed"
    ) -> bool:
        message = {
            "type": "websocket_disconnected",
            "activity_uuid": activity_uuid,
            "session_id": session_id,
            "reason": reason,
            "disconnected_at": datetime.utcnow().isoformat()
        }
        success = self.rabbitmq_client.publish(MONITORING_WEBSOCKET_EVENTS_QUEUE, message)
        if success:
            self._log(f"Evento websocket_disconnected publicado: {activity_uuid}")
        return success

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "monitoring-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)