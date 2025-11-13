import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO
from src.application.dtos.recommendation_dto import RecommendationDTO
from src.domain.value_objects.recommendation_action import RecommendationAction
from src.infrastructure.http.session_client import SessionClient
from src.infrastructure.http.content_client import ContentClient
from src.infrastructure.http.gemini_client import GeminiClient

class GenerateRecommendationUseCase:
    def __init__(self):
        self.session_client = SessionClient()
        self.content_client = ContentClient()
        self.gemini_client = GeminiClient()

    def execute(self, event: MonitoringEventDTO) -> Optional[Dict[str, Any]]:
        if not self._should_generate_recommendation(event):
            return None

        recommendation_action = self._map_event_to_action(event.evento_cognitivo)
        if recommendation_action == RecommendationAction.NADA:
            return None

        content = asyncio.run(self._fetch_or_generate_content(
            recommendation_action,
            event
        ))

        if not content:
            return None

        recommendation = RecommendationDTO(
            session_id=event.session_id,
            user_id=event.user_id,
            company_id=event.company_id,
            accion=recommendation_action.value,
            contenido={"tipo": "texto", "cuerpo": content},
            vibracion=self._extract_vibration(event),
            metadata={
                "evento_cognitivo": event.evento_cognitivo,
                "precision_cognitiva": event.precision_cognitiva,
                "confianza": event.confianza
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        return recommendation.to_dict()

    async def _fetch_or_generate_content(
        self,
        action: RecommendationAction,
        event: MonitoringEventDTO
    ) -> Optional[str]:
        activity_context = await self.session_client.get_current_activity(event.session_id)

        if activity_context:
            content = await self._search_specific_content(action, event, activity_context)
            if content:
                return content

        content = await self._search_generic_content(action, event)
        if content:
            return content

        return await self._generate_with_gemini(action, event, activity_context)

    async def _search_specific_content(
        self,
        action: RecommendationAction,
        event: MonitoringEventDTO,
        activity: Dict[str, Any]
    ) -> Optional[str]:
        title = activity.get("title")
        subtitle = activity.get("subtitle")

        if not title or not subtitle:
            return None

        result = await self.content_client.search_specific(
            recommendation_type=action.value,
            title=title,
            subtitle=subtitle,
            activity_type=event.activity_type,
            precision_min=0,
            precision_max=event.precision_cognitiva,
            evento=event.evento_cognitivo
        )

        if result:
            return result.get("contenido", {}).get("cuerpo")
        return None

    async def _search_generic_content(
        self,
        action: RecommendationAction,
        event: MonitoringEventDTO
    ) -> Optional[str]:
        result = await self.content_client.search_generic(
            recommendation_type=action.value,
            activity_type=event.activity_type,
            precision_min=0,
            precision_max=event.precision_cognitiva,
            evento=event.evento_cognitivo
        )

        if result:
            return result.get("contenido", {}).get("cuerpo")
        return None

    async def _generate_with_gemini(
        self,
        action: RecommendationAction,
        event: MonitoringEventDTO,
        activity: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        if activity:
            return await self.gemini_client.generate_specific_content(
                recommendation_type=action.value,
                title=activity.get("title", ""),
                hint=activity.get("subtitle", ""),
                objective=activity.get("content", ""),
                activity_type=event.activity_type,
                evento=event.evento_cognitivo,
                precision=event.precision_cognitiva
            )
        else:
            return await self.gemini_client.generate_generic_content(
                recommendation_type=action.value,
                activity_type=event.activity_type,
                evento=event.evento_cognitivo,
                precision=event.precision_cognitiva
            )

    def _should_generate_recommendation(self, event: MonitoringEventDTO) -> bool:
        if event.precision_cognitiva >= 0.9:
            return False
        if event.confianza < 0.5:
            return False
        return True

    def _map_event_to_action(self, evento: str) -> RecommendationAction:
        action_map = {
            "confundido": RecommendationAction.INSTRUCCION,
            "frustacion": RecommendationAction.MOTIVACION,
            "cansancio_cognitivo": RecommendationAction.PAUSA,
            "desatencion": RecommendationAction.DISTRACCION,
        }
        return action_map.get(evento.lower(), RecommendationAction.NADA)

    def _extract_vibration(self, event: MonitoringEventDTO) -> Dict[str, Any]:
        return {
            "activar": True,
            "duracion_ms": 200,
            "intensidad": "media"
        }