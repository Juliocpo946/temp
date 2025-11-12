from datetime import datetime
from src.domain.entities.activity_log import ActivityLog
from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.activity_log_repository import ActivityLogRepository

class StartActivityUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        activity_log_repo: ActivityLogRepository
    ):
        self.session_repo = session_repo
        self.activity_log_repo = activity_log_repo

    def execute(
        self,
        session_id: str,
        external_activity_id: int,
        title: str,
        subtitle: str,
        content: str,
        activity_type: str
    ) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        activity_log = ActivityLog(
            id=None,
            session_id=session.id,
            external_activity_id=external_activity_id,
            title=title,
            subtitle=subtitle,
            content=content,
            activity_type=activity_type,
            status="en_progreso",
            started_at=datetime.utcnow(),
            completed_at=None,
            feedback_data=None
        )

        created_activity = self.activity_log_repo.create(activity_log)

        session.current_activity = {
            'external_activity_id': external_activity_id,
            'title': title,
            'started_at': created_activity.started_at.isoformat()
        }
        self.session_repo.update(session)

        return {'status': 'activity_started'}