from datetime import datetime
from src.domain.entities.pause_log import PauseLog
from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.pause_log_repository import PauseLogRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class PauseSessionUseCase:
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


        event_message = {
            "type": "session_paused",
            "session_id": str(session.id),
            "timestamp": datetime.utcnow().isoformat()
        }

        self.rabbitmq_client.publish("session_events", event_message)


        self._publish_log(f"Sesion pausada: {session_id}", "info")

        return {'status': 'pausada'}

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)