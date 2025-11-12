from src.domain.repositories.session_repository import SessionRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class FinalizeSessionUseCase:
    def __init__(self, session_repo: SessionRepository, rabbitmq_client: RabbitMQClient):
        self.session_repo = session_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, session_id: str) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            self._publish_log(f"Sesion no encontrada: {session_id}", "error")
            raise ValueError("Sesion no encontrada")

        session.finalize()
        updated_session = self.session_repo.update(session)

        self._publish_log(f"Sesion finalizada: {session_id}", "info")

        return {
            'status': 'finalizada',
            'ended_at': updated_session.ended_at.isoformat()
        }

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)