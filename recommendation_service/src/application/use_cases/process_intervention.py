import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO
from src.application.dtos.recommendation_dto import RecommendationDTO
from src.domain.repositories.content_repository import ContentRepository
from src.infrastructure.http.session_client import SessionClient
from src.infrastructure.http.gemini_client import GeminiClient


class ProcessInterventionUseCase:
    def __init__(
        self,
        content_repository: ContentRepository,
        session_client: SessionClient,
        gemini_client: GeminiClient
    ):
        self.content_repository = content_repository
        self.session_client = session_client
        self.gemini_client = gemini_client

    def execute(self, event: MonitoringEventDTO) -> Optional[Dict[str, Any]]:
        activity_details = asyncio.run(
            self.session_client.get_activity_details(event.activity_uuid)
        )

        if not activity_details:
            return None

        content = self._find_content(
            tema=activity_details.get("tema"),
            subtema=activity_details.get("subtema"),
            tipo_actividad=activity_details.get("tipo_actividad"),
            tipo_intervencion=event.accion_sugerida
        )

        if not content:
            content = asyncio.run(
                self.gemini_client.generate_content(
                    tipo_intervencion=event.accion_sugerida,
                    tema=activity_details.get("tema"),
                    subtema=activity_details.get("subtema"),
                    tipo_actividad=activity_details.get("tipo_actividad"),
                    titulo=activity_details.get("titulo"),
                    objetivo=activity_details.get("objetivo"),
                    evento_cognitivo=event.evento_cognitivo,
                    precision=event.precision_cognitiva
                )
            )

        if not content:
            return None

        recommendation = RecommendationDTO(
            session_id=event.session_id,
            user_id=event.user_id,
            accion=event.accion_sugerida,
            contenido={"tipo": "texto", "cuerpo": content},
            vibracion=self._get_vibration_config(event.accion_sugerida),
            metadata={
                "evento_cognitivo": event.evento_cognitivo,
                "precision_cognitiva": event.precision_cognitiva,
                "confianza": event.confianza
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        return recommendation.to_dict()

    def _find_content(
        self,
        tema: str,
        subtema: Optional[str],
        tipo_actividad: Optional[str],
        tipo_intervencion: str
    ) -> Optional[str]:
        content = self.content_repository.find_by_criteria(
            tema=tema,
            subtema=subtema,
            tipo_actividad=tipo_actividad,
            tipo_intervencion=tipo_intervencion
        )
        if content:
            return content.contenido

        content = self.content_repository.find_by_criteria(
            tema=tema,
            tipo_actividad=tipo_actividad,
            tipo_intervencion=tipo_intervencion
        )
        if content:
            return content.contenido

        content = self.content_repository.find_by_criteria(
            tema=tema,
            tipo_intervencion=tipo_intervencion
        )
        if content:
            return content.contenido

        return None

    def _get_vibration_config(self, tipo_intervencion: str) -> Dict[str, Any]:
        configs = {
            "vibration": {"activar": True, "duracion_ms": 200, "intensidad": "media"},
            "instruction": {"activar": True, "duracion_ms": 100, "intensidad": "baja"},
            "pause": {"activar": True, "duracion_ms": 300, "intensidad": "alta"}
        }
        return configs.get(tipo_intervencion, {"activar": False, "duracion_ms": 0, "intensidad": "none"})