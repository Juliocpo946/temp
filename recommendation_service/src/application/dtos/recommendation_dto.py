from datetime import datetime
from typing import Optional, Dict, Any

class RecommendationDTO:
    def __init__(
        self,
        session_id: str,
        user_id: int,
        company_id: str,
        accion: str,
        contenido: Dict[str, Any],
        vibracion: Dict[str, Any],
        metadata: Dict[str, Any],
        timestamp: int
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.company_id = company_id
        self.accion = accion
        self.contenido = contenido
        self.vibracion = vibracion
        self.metadata = metadata
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'accion': self.accion,
            'contenido': self.contenido,
            'vibracion': self.vibracion,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }