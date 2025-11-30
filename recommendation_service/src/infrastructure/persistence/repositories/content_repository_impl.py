from typing import Optional, List
from sqlalchemy.orm import Session
from src.domain.entities.content import Content
from src.domain.repositories.content_repository import ContentRepository
from src.infrastructure.persistence.models.content_model import ContentModel


class ContentRepositoryImpl(ContentRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, content: Content) -> Content:
        model = ContentModel(
            tema=content.tema,
            subtema=content.subtema,
            tipo_actividad=content.tipo_actividad,
            tipo_intervencion=content.tipo_intervencion,
            contenido=content.contenido,
            activo=content.activo
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, content_id: int) -> Optional[Content]:
        model = self.db.query(ContentModel).filter(ContentModel.id == content_id).first()
        if not model:
            return None
        return self._to_entity(model)

    def find_by_criteria(
        self,
        tema: str,
        tipo_intervencion: str,
        subtema: Optional[str] = None,
        tipo_actividad: Optional[str] = None
    ) -> Optional[Content]:
        query = self.db.query(ContentModel).filter(
            ContentModel.tema == tema,
            ContentModel.tipo_intervencion == tipo_intervencion,
            ContentModel.activo == True
        )

        if subtema is not None:
            query = query.filter(ContentModel.subtema == subtema)
        else:
            query = query.filter(ContentModel.subtema.is_(None))

        if tipo_actividad is not None:
            query = query.filter(ContentModel.tipo_actividad == tipo_actividad)
        else:
            query = query.filter(ContentModel.tipo_actividad.is_(None))

        model = query.first()
        if not model:
            return None
        return self._to_entity(model)

    def list_all(
        self,
        tema: Optional[str] = None,
        subtema: Optional[str] = None,
        tipo_actividad: Optional[str] = None,
        tipo_intervencion: Optional[str] = None,
        activo: Optional[bool] = None
    ) -> List[Content]:
        query = self.db.query(ContentModel)

        if tema is not None:
            query = query.filter(ContentModel.tema == tema)
        if subtema is not None:
            query = query.filter(ContentModel.subtema == subtema)
        if tipo_actividad is not None:
            query = query.filter(ContentModel.tipo_actividad == tipo_actividad)
        if tipo_intervencion is not None:
            query = query.filter(ContentModel.tipo_intervencion == tipo_intervencion)
        if activo is not None:
            query = query.filter(ContentModel.activo == activo)

        models = query.all()
        return [self._to_entity(m) for m in models]

    def update(self, content: Content) -> Content:
        model = self.db.query(ContentModel).filter(ContentModel.id == content.id).first()
        if not model:
            return None

        model.tema = content.tema
        model.subtema = content.subtema
        model.tipo_actividad = content.tipo_actividad
        model.tipo_intervencion = content.tipo_intervencion
        model.contenido = content.contenido
        model.activo = content.activo

        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, content_id: int) -> bool:
        model = self.db.query(ContentModel).filter(ContentModel.id == content_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def _to_entity(self, model: ContentModel) -> Content:
        return Content(
            id=model.id,
            tema=model.tema,
            subtema=model.subtema,
            tipo_actividad=model.tipo_actividad,
            tipo_intervencion=model.tipo_intervencion,
            contenido=model.contenido,
            activo=model.activo,
            created_at=model.created_at,
            updated_at=model.updated_at
        )