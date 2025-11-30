from typing import Optional
from pydantic import BaseModel


class CreateContentDTO(BaseModel):
    tema: str
    subtema: Optional[str] = None
    tipo_actividad: Optional[str] = None
    tipo_intervencion: str
    contenido: str
    activo: bool = True


class UpdateContentDTO(BaseModel):
    tema: Optional[str] = None
    subtema: Optional[str] = None
    tipo_actividad: Optional[str] = None
    tipo_intervencion: Optional[str] = None
    contenido: Optional[str] = None
    activo: Optional[bool] = None


class ContentFilterDTO(BaseModel):
    tema: Optional[str] = None
    subtema: Optional[str] = None
    tipo_actividad: Optional[str] = None
    tipo_intervencion: Optional[str] = None
    activo: Optional[bool] = None