from src.domain.repositories.session_repository import SessionRepository
from src.application.dtos.session_dto import SessionDTO

class GetSessionUseCase:
    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo

    def execute(self, session_id: str) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        session_dto = SessionDTO(
            str(session.id),
            session.user_id,
            str(session.company_id),
            session.disability_type,
            session.cognitive_analysis_enabled,
            session.status,
            session.current_activity,
            session.created_at,
            session.last_heartbeat_at,
            session.ended_at
        )

        if session.status == "expirada":
            return {
                'session_id': str(session.id),
                'status': 'expirada',
                'codigo': 'SESSION_TIMEOUT'
            }

        return session_dto.to_dict()