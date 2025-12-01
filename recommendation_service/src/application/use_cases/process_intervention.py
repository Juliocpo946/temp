from typing import Optional, Dict, Any
from datetime import datetime
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO
from src.application.dtos.recommendation_dto import RecommendationDTO
from src.application.dtos.activity_details_dto import ActivityDetailsResponseDTO
from src.domain.repositories.content_repository import ContentRepository
from src.infrastructure.messaging.activity_details_client import ActivityDetailsClient
from src.infrastructure.messaging.session_config_client import SessionConfigClient
from src.infrastructure.http.gemini_client import GeminiClient
from src.infrastructure.cache.redis_client import RedisClient


class ProcessInterventionUseCase:
    PAUSE_MESSAGES = {
        "frustracion": "Pausar. Respirar. Regresar mejor 🧘",
        "desatencion": "Descanso corto. Regresar enfocado 💪",
        "cansancio_cognitivo": "Mente cansada. Pausa 10 minutos 😴"
    }

    INSTRUCTION_FALLBACK = {
        "frustracion": "Paso a paso. Leer despacio, entender mejor 📖",
        "desatencion": "Concentrar actividad. Tu puedes lograrlo 🎯",
        "cansancio_cognitivo": "Descanso breve. Continuar despues 💪"
    }

    def __init__(
        self,
        content_repository: ContentRepository,
        activity_details_client: ActivityDetailsClient,
        session_config_client: SessionConfigClient,
        gemini_client: GeminiClient,
        redis_client: Optional[RedisClient] = None
    ):
        self.content_repository = content_repository
        self.activity_details_client = activity_details_client
        self.session_config_client = session_config_client
        self.gemini_client = gemini_client
        self.redis_client = redis_client

    def execute(self, event: MonitoringEventDTO) -> Optional[Dict[str, Any]]:
        config = self.session_config_client.get_session_config(event.session_id)

        if not self._is_intervention_allowed(event.suggested_action, config):
            print(f"[PROCESS_INTERVENTION] [INFO] Intervencion {event.suggested_action} desactivada por config")
            return None

        if event.suggested_action == "vibration":
            return self._create_vibration_recommendation(event)

        if event.suggested_action == "pause":
            return self._create_pause_recommendation(event)

        if event.suggested_action == "instruction":
            return self._create_instruction_recommendation(event, config)

        return None

    def _is_intervention_allowed(self, intervention_type: str, config: Dict[str, Any]) -> bool:
        if intervention_type == "vibration":
            return config.get("vibration_alerts", True)
        elif intervention_type == "instruction":
            return config.get("text_notifications", True) or config.get("video_suggestions", True)
        elif intervention_type == "pause":
            return config.get("pause_suggestions", True)
        return True

    def _create_vibration_recommendation(self, event: MonitoringEventDTO) -> Dict[str, Any]:
        recommendation = RecommendationDTO(
            session_id=event.session_id,
            user_id=event.user_id,
            action="vibration",
            content=None,
            vibration={"enabled": True, "duration_ms": 200, "intensity": "medium"},
            metadata={
                "cognitive_event": event.cognitive_event,
                "cognitive_precision": event.cognitive_precision,
                "confidence": event.confidence,
                "activity_uuid": event.activity_uuid
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        print(f"[PROCESS_INTERVENTION] [INFO] Vibracion enviada para sesion: {event.session_id}")
        return recommendation.to_dict()

    def _create_pause_recommendation(self, event: MonitoringEventDTO) -> Dict[str, Any]:
        pause_message = self.PAUSE_MESSAGES.get(
            event.cognitive_event,
            "Descanso necesario. Pausa breve 🧘"
        )

        recommendation = RecommendationDTO(
            session_id=event.session_id,
            user_id=event.user_id,
            action="pause",
            content={
                "type": "text",
                "body": pause_message
            },
            vibration={"enabled": True, "duration_ms": 300, "intensity": "high"},
            metadata={
                "cognitive_event": event.cognitive_event,
                "cognitive_precision": event.cognitive_precision,
                "confidence": event.confidence,
                "activity_uuid": event.activity_uuid
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        print(f"[PROCESS_INTERVENTION] [INFO] Pausa enviada para sesion: {event.session_id}")
        return recommendation.to_dict()

    def _create_instruction_recommendation(
        self,
        event: MonitoringEventDTO,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        activity_details = self.activity_details_client.get_activity_details(
            event.activity_uuid
        )

        company_id = event.context.get("company_id") if event.context else None

        if company_id and config.get("video_suggestions", True):
            video_content = self._find_video_content(
                company_id=company_id,
                topic=activity_details.title if activity_details else None,
                subtopic=activity_details.subtitle if activity_details else None,
                activity_type=activity_details.activity_type if activity_details else None
            )

            if video_content:
                return self._build_video_recommendation(event, video_content)

        if not config.get("text_notifications", True):
            print(f"[PROCESS_INTERVENTION] [INFO] Texto desactivado y no hay video")
            return None

        text_content = None

        if activity_details:
            text_content = self.gemini_client.generate_instruction(
                topic=activity_details.title,
                subtopic=activity_details.subtitle,
                activity_type=activity_details.activity_type,
                title=activity_details.title,
                objective=activity_details.content,
                cognitive_event=event.cognitive_event,
                precision=event.cognitive_precision
            )

        if not text_content:
            text_content = self.INSTRUCTION_FALLBACK.get(
                event.cognitive_event,
                "Continuar actividad. Tu puedes 💪"
            )

        recommendation = RecommendationDTO(
            session_id=event.session_id,
            user_id=event.user_id,
            action="instruction",
            content={
                "type": "text",
                "body": text_content
            },
            vibration={"enabled": True, "duration_ms": 100, "intensity": "low"},
            metadata={
                "cognitive_event": event.cognitive_event,
                "cognitive_precision": event.cognitive_precision,
                "confidence": event.confidence,
                "activity_uuid": event.activity_uuid,
                "is_generated": text_content != self.INSTRUCTION_FALLBACK.get(event.cognitive_event)
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        print(f"[PROCESS_INTERVENTION] [INFO] Instruccion enviada para sesion: {event.session_id}")
        return recommendation.to_dict()

    def _find_video_content(
        self,
        company_id: str,
        topic: Optional[str],
        subtopic: Optional[str],
        activity_type: Optional[str]
    ) -> Optional[Any]:
        if not topic:
            return None

        content = self.content_repository.find_video_by_criteria(
            company_id=company_id,
            topic=topic,
            subtopic=subtopic,
            activity_type=activity_type,
            intervention_type="instruction"
        )
        return content

    def _build_video_recommendation(
        self,
        event: MonitoringEventDTO,
        video_content: Any
    ) -> Dict[str, Any]:
        recommendation = RecommendationDTO(
            session_id=event.session_id,
            user_id=event.user_id,
            action="instruction",
            content={
                "type": "video",
                "url": video_content.content_url
            },
            vibration={"enabled": True, "duration_ms": 100, "intensity": "low"},
            metadata={
                "cognitive_event": event.cognitive_event,
                "cognitive_precision": event.cognitive_precision,
                "confidence": event.confidence,
                "activity_uuid": event.activity_uuid,
                "content_id": video_content.id
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        print(f"[PROCESS_INTERVENTION] [INFO] Video enviado para sesion: {event.session_id}")
        return recommendation.to_dict()