from typing import Optional, List
from sqlalchemy.orm import Session as DBSession
import uuid
from src.domain.entities.activity_log import ActivityLog
from src.domain.repositories.activity_log_repository import ActivityLogRepository
from src.infrastructure.persistence.models.activity_log_model import ActivityLogModel

class ActivityLogRepositoryImpl(ActivityLogRepository):
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, activity_log: ActivityLog) -> ActivityLog:
        db_activity = ActivityLogModel(
            session_id=activity_log.session_id,
            external_activity_id=activity_log.external_activity_id,
            title=activity_log.title,
            subtitle=activity_log.subtitle,
            content=activity_log.content,
            activity_type=activity_log.activity_type,
            status=activity_log.status,
            feedback_data=activity_log.feedback_data
        )
        self.db.add(db_activity)
        self.db.commit()
        self.db.refresh(db_activity)
        return self._to_domain(db_activity)

    def get_by_session_id(self, session_id: str) -> List[ActivityLog]:
        db_activities = self.db.query(ActivityLogModel).filter(
            ActivityLogModel.session_id == uuid.UUID(session_id)
        ).all()
        return [self._to_domain(a) for a in db_activities]

    def update(self, activity_log: ActivityLog) -> ActivityLog:
        db_activity = self.db.query(ActivityLogModel).filter(
            ActivityLogModel.id == activity_log.id
        ).first()
        if db_activity:
            db_activity.status = activity_log.status
            db_activity.completed_at = activity_log.completed_at
            db_activity.feedback_data = activity_log.feedback_data
            self.db.commit()
            self.db.refresh(db_activity)
            return self._to_domain(db_activity)
        return activity_log

    @staticmethod
    def _to_domain(db_activity: ActivityLogModel) -> ActivityLog:
        return ActivityLog(
            id=db_activity.id,
            session_id=db_activity.session_id,
            external_activity_id=db_activity.external_activity_id,
            title=db_activity.title,
            subtitle=db_activity.subtitle,
            content=db_activity.content,
            activity_type=db_activity.activity_type,
            status=db_activity.status,
            started_at=db_activity.started_at,
            completed_at=db_activity.completed_at,
            feedback_data=db_activity.feedback_data
        )