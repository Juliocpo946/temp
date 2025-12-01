from typing import Optional, Dict, Any
from datetime import datetime
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO
from src.application.dtos.recommendation_dto import RecommendationDTO
from src.application.dtos.activity_details_dto import ActivityDetailsResponseDTO
from src.domain.repositories.content_repository import ContentRepository
from src.infrastructure.messaging.activity_details_client import ActivityDetailsClient
from src.infrastructure.http.gemini_client import GeminiClient
from src.infrastructure.cache.redis_client import RedisClient


class ProcessInterventionUseCase:
    def __init__(
        self,
        content_repository: ContentRepository,
        activity_details_client: ActivityDetailsClient,
        gemini_client: GeminiClient,
        redis_client: Optional[RedisClient] = None
    ):
        self.content_repository = content_repository
        self.activity_details_client = activity_details_client
        self.gemini_client = gemini_client
        self.redis_client = redis_client

    def execute(self, event: MonitoringEventDTO) -> Optional[Dict[str, Any]]:
        activity_details = self.activity_details_client.get_activity_details(
            event.activity_uuid
        )

        if not activity_details:
            print(f"[PROCESS_INTERVENTION] [ERROR] No se pudieron obtener detalles de actividad: {event.activity_uuid}")
            return self._create_default_recommendation(event)

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
            print(f"[PROCESS_INTERVENTION] [WARNING] No se pudo generar contenido, usando por defecto")
            content = self._get_default_content(event.suggested_action, event.cognitive_event)

        recommendation = RecommendationDTO(
            session_id=event.session_id,
            user_id=event.user_id,
            action=event.suggested_action,
            content={"type": "text", "body": content},
            vibration=self._get_vibration_config(event.suggested_action),
            metadata={
                "cognitive_event": event.cognitive_event,
                "cognitive_precision": event.cognitive_precision,
                "confidence": event.confidence,
                "activity_uuid": event.activity_uuid
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        print(f"[PROCESS_INTERVENTION] [INFO] Recomendacion generada para sesion: {event.session_id}")
        return recommendation.to_dict()

    def _create_default_recommendation(self, event: MonitoringEventDTO) -> Dict[str, Any]:
        content = self._get_default_content(event.suggested_action, event.cognitive_event)

        recommendation = RecommendationDTO(
            session_id=event.session_id,
            user_id=event.user_id,
            action=event.suggested_action,
            content={"type": "text", "body": content},
            vibration=self._get_vibration_config(event.suggested_action),
            metadata={
                "cognitive_event": event.cognitive_event,
                "cognitive_precision": event.cognitive_precision,
                "confidence": event.confidence,
                "activity_uuid": event.activity_uuid,
                "is_default": True
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        return recommendation.to_dict()

    def _get_default_content(self, intervention_type: str, cognitive_event: str) -> str:
        defaults = {
            "vibration": {
                "frustracion": "Respira profundo. Puedes hacerlo.",
                "desatencion": "Enfoca tu atencion en la actividad.",
                "cansancio_cognitivo": "Toma un momento para relajarte."
            },
            "instruction": {
                "frustracion": "Vamos paso a paso. Lee con calma las instrucciones.",
                "desatencion": "Concentrate en la actividad actual. Puedes lograrlo.",
                "cansancio_cognitivo": "Es normal sentirse cansado. Toma un breve descanso."
            },
            "pause": {
                "frustracion": "Es momento de pausar. Regresa cuando te sientas mejor.",
                "desatencion": "Toma una pausa corta y regresa enfocado.",
                "cansancio_cognitivo": "Tu mente necesita descanso. Pausa de 10 minutos."
            }
        }

        type_defaults = defaults.get(intervention_type, defaults["instruction"])
        return type_defaults.get(cognitive_event, "Continua con tu actividad.")

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