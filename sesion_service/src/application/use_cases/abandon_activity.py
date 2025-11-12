from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.activity_log_repository import ActivityLogRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class AbandonActivityUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        activity_log_repo: ActivityLogRepository,
        rabbitmq_client: RabbitMQClient
    ):
        self.session_repo = session_repo
        self.activity_log_repo = activity_log_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, session_id: str, external_activity_id: int) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            self._publish_log(f"Sesion no encontrada: {session_id}", "error")
            raise ValueError("Sesion no encontrada")

        activity_logs = self.activity_log_repo.get_by_session_id(session_id)
        current_activity = next(
            (a for a in activity_logs if a.external_activity_id == external_activity_id and a.status == "en_progreso"),
            None
        )

        if not current_activity:
            self._publish_log(f"Actividad no encontrada: {external_activity_id}", "error")
            raise ValueError("Actividad no encontrada")

        current_activity.abandon()
        self.activity_log_repo.update(current_activity)

        session.current_activity = None
        self.session_repo.update(session)

        self._publish_log(f"Actividad abandonada: {external_activity_id}", "info")

        return {'status': 'abandonada'}

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)