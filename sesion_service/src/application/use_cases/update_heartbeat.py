from src.domain.repositories.session_repository import SessionRepository

class UpdateHeartbeatUseCase:
    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo

    def execute(self, session_id: str) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        session.update_heartbeat()
        updated_session = self.session_repo.update(session)

        return {
            'status': 'ok',
            'last_heartbeat_at': updated_session.last_heartbeat_at.isoformat()
        }