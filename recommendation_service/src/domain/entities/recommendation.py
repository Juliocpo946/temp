from datetime import datetime
from typing import Optional
import uuid

class Recommendation:
    def __init__(
        self,
        id: Optional[str],
        session_id: str,
        user_id: int,
        company_id: str,
        accion: str,
        contenido: dict,
        vibracion: dict,
        metadata: dict,
        created_at: datetime
    ):
        self.id = id or str(uuid.uuid4())
        self.session_id = session_id
        self.user_id = user_id
        self.company_id = company_id
        self.accion = accion
        self.contenido = contenido
        self.vibracion = vibracion
        self.metadata = metadata
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'accion': self.accion,
            'contenido': self.contenido,
            'vibracion': self.vibracion,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }