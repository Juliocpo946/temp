from typing import Dict, Any

class MonitoringEventDTO:
    def __init__(
        self,
        session_id: str,
        user_id: int,
        external_activity_id: int,
        activity_uuid: str,
        intervention_type: str,
        confidence: float,
        context: Dict[str, Any],
        timestamp: int
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.external_activity_id = external_activity_id
        self.activity_uuid = activity_uuid
        self.intervention_type = intervention_type
        self.confidence = confidence
        self.context = context
        self.timestamp = timestamp

    @property
    def evento_cognitivo(self) -> str:
        mapping = {
            "vibration": "desatencion",
            "instruction": "frustracion",
            "pause": "cansancio_cognitivo"
        }
        return mapping.get(self.intervention_type, "desconocido")

    @property
    def accion_sugerida(self) -> str:
        return self.intervention_type

    @property
    def precision_cognitiva(self) -> float:
        return self.context.get("precision_cognitiva", 0.5)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "external_activity_id": self.external_activity_id,
            "activity_uuid": self.activity_uuid,
            "evento_cognitivo": self.evento_cognitivo,
            "accion_sugerida": self.accion_sugerida,
            "precision_cognitiva": self.precision_cognitiva,
            "confianza": self.confidence,
            "contexto": self.context,
            "timestamp": self.timestamp
        }