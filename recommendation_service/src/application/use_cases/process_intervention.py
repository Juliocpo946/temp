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
        "frustracion": "Pausar. Respirar. Regresar mejor",
        "desatencion": "Descanso corto. Regresar enfocado",
        "cansancio_cognitivo": "Mente cansada. Pausa 10 minutos"
    }

    INSTRUCTION_FALLBACK = {
        "frustracion": "Paso a paso. Leer despacio, entender mejor",
        "desatencion": "Concentrar actividad. Tu puedes lograrlo",
        "cansancio_cognitivo": "Descanso breve. Continuar despues"
    }

    def __init__(
        self,
        content_repository: ContentRepository,
        activity_details_client: ActivityDetailsClient,
        session_config_client: SessionConfigClient,
        gemini_client: GeminiClient,
        redis_client: RedisClient
    ):
        self.content_repository = content_repository
        self.activity_details_client = activity_details_client
        self.session_config_client = session_config_client
        self.gemini_client = gemini_client
        self.redis_client = redis_client

    def execute(self, event: MonitoringEventDTO) -> Optional[Dict[str, Any]]:
        config = self.session_config_client.get_session_config(event.session_id)

        if not config.get("cognitive_analysis_enabled", True):
            return None

        action = event.accion_sugerida

        if action == "vibration" and not config.get("vibration_alerts", True):
            return None
        if action == "instruction" and not config.get("text_notifications", True):
            return None
        if action == "pause" and not config.get("pause_suggestions", True):
            return None

        activity_details = self._get_activity_details(event)

        topic = activity_details.topic if activity_details else "general"
        content_type = self._determine_content_type(action, event.evento_cognitivo)
        
        if self._should_avoid_content(topic, event.evento_cognitivo, content_type):
            content_type = self._get_alternative_content_type(content_type)

        content = self._generate_content(
            action=action,
            cognitive_event=event.evento_cognitivo,
            activity_details=activity_details,
            precision=event.precision_cognitiva,
            config=config
        )

        vibration_pattern = self._get_vibration_pattern(action, event.evento_cognitivo)

        recommendation = {
            "session_id": event.session_id,
            "user_id": event.user_id,
            "action": action,
            "content": content,
            "vibration": vibration_pattern,
            "metadata": {
                "cognitive_event": event.evento_cognitivo,
                "precision": event.precision_cognitiva,
                "confidence": event.confianza,
                "topic": topic,
                "content_type": content_type
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        return recommendation

    def _get_activity_details(self, event: MonitoringEventDTO) -> Optional[ActivityDetailsResponseDTO]:
        try:
            activity_uuid = event.contexto.get("activity_uuid") if event.contexto else None
            if not activity_uuid:
                return None

            return self.activity_details_client.get_activity_details(activity_uuid)
        except Exception as e:
            print(f"[PROCESS_INTERVENTION] [ERROR] Error obteniendo detalles de actividad: {str(e)}")
            return None

    def _determine_content_type(self, action: str, cognitive_event: str) -> str:
        if action == "pause":
            return "pause_suggestion"
        elif action == "instruction":
            return "text_instruction"
        elif action == "vibration":
            return "vibration_only"
        return "generic"

    def _should_avoid_content(self, topic: str, cognitive_event: str, content_type: str) -> bool:
        evaluations = self.redis_client.get_intervention_evaluations_for_topic(topic, limit=5)
        if not evaluations:
            return False
        
        negative_count = sum(
            1 for e in evaluations 
            if e.get("result") in ["negative", "sin_efecto"] 
            and e.get("content_type") == content_type
            and e.get("cognitive_event") == cognitive_event
        )
        
        return negative_count >= 3

    def _get_alternative_content_type(self, original_type: str) -> str:
        alternatives = {
            "text_instruction": "video_suggestion",
            "video_suggestion": "text_instruction",
            "pause_suggestion": "break_activity"
        }
        return alternatives.get(original_type, original_type)

    def _generate_content(
        self,
        action: str,
        cognitive_event: str,
        activity_details: Optional[ActivityDetailsResponseDTO],
        precision: float,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if action == "pause":
            return {
                "type": "pause",
                "message": self.PAUSE_MESSAGES.get(cognitive_event, "Tomar descanso. Regresar pronto"),
                "duration_suggestion": 300
            }

        if action == "vibration":
            return {
                "type": "vibration",
                "message": None
            }

        if action == "instruction":
            topic = activity_details.topic if activity_details else "general"
            subtopic = activity_details.subtopic if activity_details else None
            activity_type = activity_details.activity_type if activity_details else None
            title = activity_details.title if activity_details else None
            objective = activity_details.objective if activity_details else None

            generated_instruction = None
            if self.gemini_client:
                generated_instruction = self.gemini_client.generate_instruction(
                    topic=topic,
                    subtopic=subtopic,
                    activity_type=activity_type,
                    title=title,
                    objective=objective,
                    cognitive_event=cognitive_event,
                    precision=precision
                )

            if generated_instruction:
                return {
                    "type": "instruction",
                    "message": generated_instruction,
                    "source": "generated"
                }

            fallback_message = self.INSTRUCTION_FALLBACK.get(
                cognitive_event,
                "Continuar con calma. Tu puedes"
            )
            return {
                "type": "instruction",
                "message": fallback_message,
                "source": "fallback"
            }

        return None

    def _get_vibration_pattern(self, action: str, cognitive_event: str) -> Optional[Dict[str, Any]]:
        patterns = {
            "vibration": {
                "desatencion": {"pattern": [200, 100, 200], "intensity": "medium"},
                "default": {"pattern": [300], "intensity": "light"}
            },
            "instruction": {
                "frustracion": {"pattern": [100, 50, 100, 50, 100], "intensity": "gentle"},
                "default": {"pattern": [150, 75, 150], "intensity": "light"}
            },
            "pause": {
                "cansancio_cognitivo": {"pattern": [500, 200, 500], "intensity": "strong"},
                "default": {"pattern": [400, 150, 400], "intensity": "medium"}
            }
        }

        action_patterns = patterns.get(action, {})
        return action_patterns.get(cognitive_event, action_patterns.get("default"))