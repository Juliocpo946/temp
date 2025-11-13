from pydantic import BaseModel
from typing import Dict, Any, Optional

class RecommendationResponseSchema(BaseModel):
    session_id: str
    user_id: int
    company_id: str
    accion: str
    contenido: Dict[str, Any]
    vibracion: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: int

    class Config:
        from_attributes = True