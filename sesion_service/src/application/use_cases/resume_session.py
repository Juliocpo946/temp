from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.pause_log_repository import PauseLogRepository

class ResumeSessionUseCase:
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

        session.resume()
        session.update_heartbeat()
        self.session_repo.update(session)

        active_pause = self.pause_log_repo.get_active_pause(session_id)
        if active_pause:
            active_pause.end()
            self.pause_log_repo.update(active_pause)

        return {'status': 'activa'}