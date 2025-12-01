import json
from datetime import datetime
from typing import Dict, Any, Optional
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import INTERVENTION_EVALUATIONS_QUEUE, LOG_SERVICE_QUEUE


class InterventionEvaluationPublisher:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.rabbitmq_client = rabbitmq_client

    def publish_evaluation(
        self,
        intervention_id: str,
        session_id: str,
        activity_uuid: str,
        cognitive_event: str,
        intervention_type: str,
        result: str,
        topic: Optional[str] = None,
        content_type: Optional[str] = None,
        precision_before: Optional[float] = None,
        precision_after: Optional[float] = None
    ) -> bool:
        message = {
            "type": "intervention_evaluation",
            "intervention_id": intervention_id,
            "session_id": session_id,
            "activity_uuid": activity_uuid,
            "cognitive_event": cognitive_event,
            "intervention_type": intervention_type,
            "result": result,
            "topic": topic,
            "content_type": content_type,
            "precision_before": precision_before,
            "precision_after": precision_after,
            "evaluated_at": datetime.utcnow().isoformat()
        }

        success = self.rabbitmq_client.publish(INTERVENTION_EVALUATIONS_QUEUE, message)
        
        if success:
            self._log(f"Evaluacion de intervencion publicada: {intervention_id} -> {result}")
        else:
            self._log(f"Error publicando evaluacion de intervencion: {intervention_id}", "error")
        
        return success

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "monitoring-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)