import json
from typing import Optional
from datetime import datetime
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import MONITORING_EVENTS_QUEUE, LOG_SERVICE_QUEUE
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO


class MonitoringPublisher:
    _instance = None
    _rabbitmq_client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._rabbitmq_client = RabbitMQClient()
        return cls._instance

    def publish(self, event: MonitoringEventDTO, correlation_id: Optional[str] = None) -> bool:
        # Agregar activity_uuid al contexto para que el recommendation_service lo reciba
        contexto = event.contexto.copy() if event.contexto else {}
        contexto["activity_uuid"] = event.activity_uuid
        
        message = {
            "session_id": event.session_id,
            "user_id": event.user_id,
            "external_activity_id": event.external_activity_id,
            "activity_uuid": event.activity_uuid,
            "evento_cognitivo": event.evento_cognitivo,
            "accion_sugerida": event.accion_sugerida,
            "precision_cognitiva": event.precision_cognitiva,
            "confianza": event.confianza,
            "contexto": contexto,
            "timestamp": event.timestamp,
            "correlation_id": correlation_id,
            "published_at": datetime.utcnow().isoformat()
        }

        success = self._rabbitmq_client.publish(
            MONITORING_EVENTS_QUEUE, 
            message, 
            correlation_id=correlation_id
        )

        if success:
            self._log(
                f"Evento publicado: session={event.session_id}, activity={event.activity_uuid}, evento={event.evento_cognitivo}, correlation_id={correlation_id}",
                correlation_id=correlation_id
            )
        else:
            self._log(
                f"Error publicando evento: session={event.session_id}",
                level="error",
                correlation_id=correlation_id
            )

        return success

    def _log(self, message: str, level: str = "info", correlation_id: Optional[str] = None) -> None:
        log_message = {
            "service": "monitoring-service",
            "level": level,
            "message": message,
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message, correlation_id=correlation_id)