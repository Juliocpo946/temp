from datetime import datetime
from typing import Optional


class Content:
    def __init__(
        self,
        id: Optional[int],
        tema: str,
        subtema: Optional[str],
        tipo_actividad: Optional[str],
        tipo_intervencion: str,
        contenido: str,
        activo: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.tema = tema
        self.subtema = subtema
        self.tipo_actividad = tipo_actividad
        self.tipo_intervencion = tipo_intervencion
        self.contenido = contenido
        self.activo = activo
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def update(
        self,
        tema: Optional[str] = None,
        subtema: Optional[str] = None,
        tipo_actividad: Optional[str] = None,
        tipo_intervencion: Optional[str] = None,
        contenido: Optional[str] = None,
        activo: Optional[bool] = None
    ) -> None:
        if tema is not None:
            self.tema = tema
        if subtema is not None:
            self.subtema = subtema
        if tipo_actividad is not None:
            self.tipo_actividad = tipo_actividad
        if tipo_intervencion is not None:
            self.tipo_intervencion = tipo_intervencion
        if contenido is not None:
            self.contenido = contenido
        if activo is not None:
            self.activo = activo
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tema": self.tema,
            "subtema": self.subtema,
            "tipo_actividad": self.tipo_actividad,
            "tipo_intervencion": self.tipo_intervencion,
            "contenido": self.contenido,
            "activo": self.activo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }