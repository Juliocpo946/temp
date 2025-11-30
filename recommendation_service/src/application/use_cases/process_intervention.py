from typing import Optional, Dict, Any
from datetime import datetime
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO
from src.application.dtos.recommendation_dto import RecommendationDTO
from src.application.dtos.activity_details_dto import ActivityDetailsResponseDTO
from src.domain.repositories.content_repository import ContentRepository
from src.infrastructure.messaging.activity_details_client import ActivityDetailsClient
from src.infrastructure.http.gemini_client import GeminiClient


class ProcessInterventionUseCase:
    def __init__(
        self,
        content_repository: ContentRepository,
        activity_details_client: ActivityDetailsClient,
        gemini_client: GeminiClient
    ):
        self.content_repository = content_repository
        self.activity_details_client = activity_details_client
        self.gemini_client = gemini_client

    def execute(self, event: MonitoringEventDTO) -> Optional[Dict[str, Any]]:
        activity_details = self.activity_details_client.get_activity_details(
            event.activity_uuid
        )

        if not activity_details:
            print(f"[PROCESS_INTERVENTION] [ERROR] No se pudieron obtener detalles de actividad: {event.activity_uuid}")
            return None

        content = self._find_content(
            topic=activity_details.title,
            subtopic=activity_details.subtitle,
            activity_type=activity_details.activity_type,
            intervention_type=event.suggested_action
        )

        if not content:
            content = self.gemini_client.generate_content(
                intervention_type=event.suggested_action,
                topic=activity_details.title,
                subtopic=activity_details.subtitle,
                activity_type=activity_details.activity_type,
                title=activity_details.title,
                objective=activity_details.content,
                cognitive_event=event.cognitive_event,
                precision=event.cognitive_precision
            )

        if not content:
            print(f"[PROCESS_INTERVENTION] [ERROR] No se pudo generar contenido para la intervencion")
            return None

        recommendation = RecommendationDTO(
            session_id=event.session_id,
            user_id=event.user_id,
            action=event.suggested_action,
            content={"type": "text", "body": content},
            vibration=self._get_vibration_config(event.suggested_action),
            metadata={
                "cognitive_event": event.cognitive_event,
                "cognitive_precision": event.cognitive_precision,
                "confidence": event.confidence
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        print(f"[PROCESS_INTERVENTION] [INFO] Recomendacion generada para sesion: {event.session_id}")
        return recommendation.to_dict()

    def _find_content(
        self,
        topic: str,
        subtopic: Optional[str],
        activity_type: Optional[str],
        intervention_type: str
    ) -> Optional[str]:
        content = self.content_repository.find_by_criteria(
            topic=topic,
            subtopic=subtopic,
            activity_type=activity_type,
            intervention_type=intervention_type
        )
        if content:
            return content.content

        content = self.content_repository.find_by_criteria(
            topic=topic,
            activity_type=activity_type,
            intervention_type=intervention_type
        )
        if content:
            return content.content

        content = self.content_repository.find_by_criteria(
            topic=topic,
            intervention_type=intervention_type
        )
        if content:
            return content.content

        return None

    def _get_vibration_config(self, intervention_type: str) -> Dict[str, Any]:
        configs = {
            "vibration": {"enabled": True, "duration_ms": 200, "intensity": "medium"},
            "instruction": {"enabled": True, "duration_ms": 100, "intensity": "low"},
            "pause": {"enabled": True, "duration_ms": 300, "intensity": "high"}
        }
        return configs.get(intervention_type, {"enabled": False, "duration_ms": 0, "intensity": "none"})