from src.domain.repositories.session_repository import SessionRepository
from src.application.dtos.session_dto import SessionDTO
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class GetSessionUseCase:
    def __init__(self, session_repo: SessionRepository, rabbitmq_client: RabbitMQClient):
        self.session_repo = session_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, session_id: str) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            self._publish_log(f"Sesion no encontrada: {session_id}", "error")
            raise ValueError("Sesion no encontrada")

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

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)