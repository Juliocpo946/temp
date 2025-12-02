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

    # --- PROPIEDADES ALIAS ---
    @property
    def evento_cognitivo(self) -> str:
        return self._map_intervention_to_evento()

    @property
    def accion_sugerida(self) -> str:
        return self.intervention_type

    @property
    def precision_cognitiva(self) -> float:
        return self.context.get("precision_cognitiva", 0.0)

    @property
    def confianza(self) -> float:
        return self.confidence

    @property
    def contexto(self) -> Dict[str, Any]:
        return self.context
    # -------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "external_activity_id": self.external_activity_id,
            "activity_uuid": self.activity_uuid,
            "evento_cognitivo": self.evento_cognitivo, # Usa la propiedad
            "accion_sugerida": self.accion_sugerida,   # Usa la propiedad
            "precision_cognitiva": self.precision_cognitiva, # Usa la propiedad
            "confianza": self.confianza,               # Usa la propiedad
            "contexto": self.contexto,                 # Usa la propiedad
            "timestamp": self.timestamp
        }

    def _map_intervention_to_evento(self) -> str:
        mapping = {
            "vibration": "desatencion",
            "instruction": "frustracion",
            "pause": "cansancio_cognitivo"
        }
        # Manejo robusto para Enum o string
        val = getattr(self.intervention_type, "value", self.intervention_type)
        if hasattr(val, "lower"):
             val = val.lower()
        return mapping.get(val, "desconocido")