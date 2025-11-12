from src.domain.repositories.session_repository import SessionRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class UpdateHeartbeatUseCase:
    def __init__(self, session_repo: SessionRepository, rabbitmq_client: RabbitMQClient):
        self.session_repo = session_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, session_id: str) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            self._publish_log(f"Sesion no encontrada: {session_id}", "error")
            raise ValueError("Sesion no encontrada")

        session.update_heartbeat()
        updated_session = self.session_repo.update(session)

        return {
            'status': 'ok',
            'last_heartbeat_at': updated_session.last_heartbeat_at.isoformat()
        }

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)