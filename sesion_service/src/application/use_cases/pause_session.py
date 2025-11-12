from datetime import datetime
from src.domain.entities.pause_log import PauseLog
from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.pause_log_repository import PauseLogRepository

class PauseSessionUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        pause_log_repo: PauseLogRepository
    ):
        self.session_repo = session_repo
        self.pause_log_repo = pause_log_repo

    def execute(self, session_id: str) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        session.pause()
        self.session_repo.update(session)

        pause_log = PauseLog(
            id=None,
            session_id=session.id,
            pause_type="manual",
            started_at=datetime.utcnow(),
            ended_at=None
        )
        self.pause_log_repo.create(pause_log)

        return {'status': 'pausada'}