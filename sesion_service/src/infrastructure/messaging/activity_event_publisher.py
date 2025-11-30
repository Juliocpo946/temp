from datetime import datetime
from typing import Dict, Any
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import ACTIVITY_EVENTS_QUEUE, LOG_SERVICE_QUEUE

class ActivityEventPublisher:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.rabbitmq_client = rabbitmq_client

    def publish_activity_created(
        self,
        activity_uuid: str,
        session_id: str,
        external_activity_id: int,
        user_id: int
    ) -> bool:
        message = {
            "type": "activity_created",
            "activity_uuid": activity_uuid,
            "session_id": session_id,
            "external_activity_id": external_activity_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        success = self.rabbitmq_client.publish(ACTIVITY_EVENTS_QUEUE, message)
        if success:
            self._log(f"Evento activity_created publicado: {activity_uuid}")
        return success

    def publish_activity_paused(self, activity_uuid: str, session_id: str) -> bool:
        message = {
            "type": "activity_paused",
            "activity_uuid": activity_uuid,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        success = self.rabbitmq_client.publish(ACTIVITY_EVENTS_QUEUE, message)
        if success:
            self._log(f"Evento activity_paused publicado: {activity_uuid}")
        return success

    def publish_activity_resumed(self, activity_uuid: str, session_id: str) -> bool:
        message = {
            "type": "activity_resumed",
            "activity_uuid": activity_uuid,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        success = self.rabbitmq_client.publish(ACTIVITY_EVENTS_QUEUE, message)
        if success:
            self._log(f"Evento activity_resumed publicado: {activity_uuid}")
        return success

    def publish_activity_completed(self, activity_uuid: str, session_id: str) -> bool:
        message = {
            "type": "activity_completed",
            "activity_uuid": activity_uuid,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        success = self.rabbitmq_client.publish(ACTIVITY_EVENTS_QUEUE, message)
        if success:
            self._log(f"Evento activity_completed publicado: {activity_uuid}")
        return success

    def publish_activity_abandoned(self, activity_uuid: str, session_id: str) -> bool:
        message = {
            "type": "activity_abandoned",
            "activity_uuid": activity_uuid,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        success = self.rabbitmq_client.publish(ACTIVITY_EVENTS_QUEUE, message)
        if success:
            self._log(f"Evento activity_abandoned publicado: {activity_uuid}")
        return success

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "session-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)