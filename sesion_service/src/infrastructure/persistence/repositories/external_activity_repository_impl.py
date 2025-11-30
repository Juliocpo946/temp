from typing import Optional
from sqlalchemy.orm import Session as DBSession
from src.domain.entities.external_activity import ExternalActivity
from src.domain.repositories.external_activity_repository import ExternalActivityRepository
from src.infrastructure.persistence.models.external_activity_model import ExternalActivityModel

class ExternalActivityRepositoryImpl(ExternalActivityRepository):
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, activity: ExternalActivity) -> ExternalActivity:
        db_activity = ExternalActivityModel(
            external_activity_id=activity.external_activity_id,
            title=activity.title,
            subtitle=activity.subtitle,
            content=activity.content,
            activity_type=activity.activity_type
        )
        self.db.add(db_activity)
        self.db.commit()
        self.db.refresh(db_activity)
        return self._to_domain(db_activity)

    def get_by_external_id(self, external_activity_id: int) -> Optional[ExternalActivity]:
        db_activity = self.db.query(ExternalActivityModel).filter(
            ExternalActivityModel.external_activity_id == external_activity_id
        ).first()
        return self._to_domain(db_activity) if db_activity else None

    def get_or_create(
        self,
        external_activity_id: int,
        title: str,
        subtitle: Optional[str],
        content: Optional[str],
        activity_type: str
    ) -> ExternalActivity:
        existing = self.get_by_external_id(external_activity_id)
        if existing:
            return existing
        
        activity = ExternalActivity(
            id=None,
            external_activity_id=external_activity_id,
            title=title,
            subtitle=subtitle,
            content=content,
            activity_type=activity_type
        )
        return self.create(activity)

    @staticmethod
    def _to_domain(db_activity: ExternalActivityModel) -> ExternalActivity:
        return ExternalActivity(
            id=db_activity.id,
            external_activity_id=db_activity.external_activity_id,
            title=db_activity.title,
            subtitle=db_activity.subtitle,
            content=db_activity.content,
            activity_type=db_activity.activity_type
        )