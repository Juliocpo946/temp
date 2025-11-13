from datetime import datetime
from typing import Optional

class MonitoringEventDTO:
    def __init__(
        self,
        session_id: str,
        user_id: int,
        company_id: str,
        timestamp: int,
        evento_cognitivo: str,
        precision_cognitiva: float,
        confianza: float,
        tiempo_en_actividad: int,
        activity_type: str,
        external_activity_id: int,
        intentos_fallidos: Optional[int] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.company_id = company_id
        self.timestamp = timestamp
        self.evento_cognitivo = evento_cognitivo
        self.precision_cognitiva = precision_cognitiva
        self.confianza = confianza
        self.tiempo_en_actividad = tiempo_en_actividad
        self.activity_type = activity_type
        self.external_activity_id = external_activity_id
        self.intentos_fallidos = intentos_fallidos

    @staticmethod
    def from_dict(data: dict) -> 'MonitoringEventDTO':
        return MonitoringEventDTO(
            session_id=data.get('session_id'),
            user_id=data.get('user_id'),
            company_id=data.get('company_id'),
            timestamp=data.get('timestamp'),
            evento_cognitivo=data.get('evento_cognitivo'),
            precision_cognitiva=data.get('precision_cognitiva'),
            confianza=data.get('confianza'),
            tiempo_en_actividad=data.get('tiempo_en_actividad'),
            activity_type=data.get('activity_type'),
            external_activity_id=data.get('external_activity_id'),
            intentos_fallidos=data.get('intentos_fallidos')
        )