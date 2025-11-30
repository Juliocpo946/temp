from typing import Dict, Any, Optional


class MonitoringEventDTO:
    def __init__(
        self,
        session_id: str,
        user_id: int,
        activity_uuid: str,
        evento_cognitivo: str,
        accion_sugerida: str,
        precision_cognitiva: float,
        confianza: float,
        contexto: Dict[str, Any],
        timestamp: int
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.activity_uuid = activity_uuid
        self.evento_cognitivo = evento_cognitivo
        self.accion_sugerida = accion_sugerida
        self.precision_cognitiva = precision_cognitiva
        self.confianza = confianza
        self.contexto = contexto
        self.timestamp = timestamp

    @staticmethod
    def from_dict(data: dict) -> 'MonitoringEventDTO':
        return MonitoringEventDTO(
            session_id=data.get('session_id'),
            user_id=data.get('user_id'),
            activity_uuid=data.get('activity_uuid'),
            evento_cognitivo=data.get('evento_cognitivo'),
            accion_sugerida=data.get('accion_sugerida'),
            precision_cognitiva=data.get('precision_cognitiva', 0.0),
            confianza=data.get('confianza', 0.0),
            contexto=data.get('contexto', {}),
            timestamp=data.get('timestamp', 0)
        )