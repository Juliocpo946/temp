from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.pause_log_repository import PauseLogRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class ResumeSessionUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        pause_log_repo: PauseLogRepository,
        rabbitmq_client: RabbitMQClient
    ):
        self.session_repo = session_repo
        self.pause_log_repo = pause_log_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, session_id: str) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            self._publish_log(f"Sesion no encontrada: {session_id}", "error")
            raise ValueError("Sesion no encontrada")

        session.resume()
        session.update_heartbeat()
        self.session_repo.update(session)

        active_pause = self.pause_log_repo.get_active_pause(session_id)
        if active_pause:
            active_pause.end()
            self.pause_log_repo.update(active_pause)

        self._publish_log(f"Sesion reanudada: {session_id}", "info")

        return {'status': 'activa'}

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)