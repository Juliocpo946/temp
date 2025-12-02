from typing import Dict, Any


class MonitoringEventDTO:
    def __init__(
        self,
        session_id: str,
        user_id: int,
        activity_uuid: str,
        external_activity_id: int,
        cognitive_event: str,
        suggested_action: str,
        cognitive_precision: float,
        confidence: float,
        context: Dict[str, Any],
        timestamp: int
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.activity_uuid = activity_uuid
        self.external_activity_id = external_activity_id
        self.cognitive_event = cognitive_event
        self.suggested_action = suggested_action
        self.cognitive_precision = cognitive_precision
        self.confidence = confidence
        self.context = context
        self.timestamp = timestamp

    # --- PROPIEDADES ALIAS (Corrección para compatibilidad) ---
    @property
    def evento_cognitivo(self) -> str:
        return self.cognitive_event

    @property
    def accion_sugerida(self) -> str:
        return self.suggested_action

    @property
    def precision_cognitiva(self) -> float:
        return self.cognitive_precision

    @property
    def confianza(self) -> float:
        return self.confidence

    @property
    def contexto(self) -> Dict[str, Any]:
        return self.context
    # ---------------------------------------------------------

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonitoringEventDTO":
        return cls(
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            activity_uuid=data.get("activity_uuid"),
            external_activity_id=data.get("external_activity_id"),
            cognitive_event=data.get("evento_cognitivo", data.get("cognitive_event")),
            suggested_action=data.get("accion_sugerida", data.get("suggested_action")),
            cognitive_precision=data.get("precision_cognitiva", data.get("cognitive_precision", 0.5)),
            confidence=data.get("confianza", data.get("confidence", 0.5)),
            context=data.get("contexto", data.get("context", {})),
            timestamp=data.get("timestamp")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "activity_uuid": self.activity_uuid,
            "external_activity_id": self.external_activity_id,
            "cognitive_event": self.cognitive_event,
            "suggested_action": self.suggested_action,
            "cognitive_precision": self.cognitive_precision,
            "confidence": self.confidence,
            "context": self.context,
            "timestamp": self.timestamp
        }