from typing import Dict, Any
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import MONITORING_EVENTS_QUEUE, LOG_SERVICE_QUEUE
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO

class MonitoringPublisher:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()

    def publish_intervention(self, event: MonitoringEventDTO) -> bool:
        message = event.to_dict()
        success = self.rabbitmq_client.publish(MONITORING_EVENTS_QUEUE, message)
        if success:
            self._log(f"Intervencion publicada: {event.intervention_type} para sesion {event.session_id}")
        return success

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "monitoring-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)

    def close(self) -> None:
        self.rabbitmq_client.close()