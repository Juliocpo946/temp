from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.activity_log_repository import ActivityLogRepository

class CompleteActivityUseCase:
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
        feedback: dict
    ) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        activity_logs = self.activity_log_repo.get_by_session_id(session_id)
        current_activity = next(
            (a for a in activity_logs if a.external_activity_id == external_activity_id and a.status == "en_progreso"),
            None
        )

        if not current_activity:
            raise ValueError("Activity not found or already completed")

        current_activity.complete(feedback)
        self.activity_log_repo.update(current_activity)

        session.current_activity = None
        self.session_repo.update(session)

        return {'status': 'completada'}