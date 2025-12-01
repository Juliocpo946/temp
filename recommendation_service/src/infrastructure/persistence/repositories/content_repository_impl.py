from typing import Optional, List
from sqlalchemy.orm import Session
import uuid
from src.domain.entities.content import Content
from src.domain.repositories.content_repository import ContentRepository
from src.infrastructure.persistence.models.content_model import ContentModel


class ContentRepositoryImpl(ContentRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, content: Content) -> Content:
        model = ContentModel(
            company_id=content.company_id,
            topic=content.topic,
            subtopic=content.subtopic,
            activity_type=content.activity_type,
            intervention_type=content.intervention_type,
            content_url=content.content_url,
            content_type=content.content_type,
            active=content.active
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
        company_id: str,
        topic: str,
        intervention_type: str,
        subtopic: Optional[str] = None,
        activity_type: Optional[str] = None
    ) -> Optional[Content]:
        query = self.db.query(ContentModel).filter(
            ContentModel.company_id == uuid.UUID(company_id),
            ContentModel.topic == topic,
            ContentModel.intervention_type == intervention_type,
            ContentModel.active == True
        )

        if subtopic is not None:
            query = query.filter(ContentModel.subtopic == subtopic)

        if activity_type is not None:
            query = query.filter(ContentModel.activity_type == activity_type)

        model = query.first()
        if not model:
            return None
        return self._to_entity(model)

    def find_video_by_criteria(
        self,
        company_id: str,
        topic: str,
        intervention_type: str,
        subtopic: Optional[str] = None,
        activity_type: Optional[str] = None
    ) -> Optional[Content]:
        query = self.db.query(ContentModel).filter(
            ContentModel.company_id == uuid.UUID(company_id),
            ContentModel.topic == topic,
            ContentModel.intervention_type == intervention_type,
            ContentModel.content_type == "video",
            ContentModel.active == True
        )

        if subtopic is not None:
            result = query.filter(ContentModel.subtopic == subtopic).first()
            if result:
                return self._to_entity(result)

        if activity_type is not None:
            result = query.filter(ContentModel.activity_type == activity_type).first()
            if result:
                return self._to_entity(result)

        result = query.first()
        if result:
            return self._to_entity(result)

        return None

    def list_all(
        self,
        company_id: Optional[str] = None,
        topic: Optional[str] = None,
        subtopic: Optional[str] = None,
        activity_type: Optional[str] = None,
        intervention_type: Optional[str] = None,
        active: Optional[bool] = None
    ) -> List[Content]:
        query = self.db.query(ContentModel)

        if company_id is not None:
            query = query.filter(ContentModel.company_id == uuid.UUID(company_id))
        if topic is not None:
            query = query.filter(ContentModel.topic == topic)
        if subtopic is not None:
            query = query.filter(ContentModel.subtopic == subtopic)
        if activity_type is not None:
            query = query.filter(ContentModel.activity_type == activity_type)
        if intervention_type is not None:
            query = query.filter(ContentModel.intervention_type == intervention_type)
        if active is not None:
            query = query.filter(ContentModel.active == active)

        models = query.all()
        return [self._to_entity(m) for m in models]

    def update(self, content: Content) -> Content:
        model = self.db.query(ContentModel).filter(ContentModel.id == content.id).first()
        if not model:
            return None

        model.topic = content.topic
        model.subtopic = content.subtopic
        model.activity_type = content.activity_type
        model.intervention_type = content.intervention_type
        model.content_url = content.content_url
        model.content_type = content.content_type
        model.active = content.active

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
            company_id=model.company_id,
            topic=model.topic,
            subtopic=model.subtopic,
            activity_type=model.activity_type,
            intervention_type=model.intervention_type,
            content_url=model.content_url,
            content_type=model.content_type,
            active=model.active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )