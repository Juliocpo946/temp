from datetime import datetime
from src.domain.entities.activity_log import ActivityLog
from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.activity_log_repository import ActivityLogRepository
from src.domain.repositories.external_activity_repository import ExternalActivityRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class StartActivityUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        activity_log_repo: ActivityLogRepository,
        external_activity_repo: ExternalActivityRepository,
        rabbitmq_client: RabbitMQClient
    ):
        self.session_repo = session_repo
        self.activity_log_repo = activity_log_repo
        self.external_activity_repo = external_activity_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(
        self,
        session_id: str,
        external_activity_id: int,
        title: str,
        subtitle: str,
        content: str,
        activity_type: str
    ) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            self._publish_log(f"Sesion no encontrada: {session_id}", "error")
            raise ValueError("Sesion no encontrada")

        external_activity = self.external_activity_repo.get_or_create(
            external_activity_id,
            title,
            subtitle,
            content,
            activity_type
        )

        activity_log = ActivityLog(
            id=None,
            session_id=session.id,
            external_activity_id=external_activity_id,
            status="en_progreso",
            started_at=datetime.utcnow(),
            completed_at=None,
            feedback_data=None
        )

        created_activity = self.activity_log_repo.create(activity_log)

        session.current_activity = {
            'external_activity_id': external_activity_id,
            'title': title,
            'started_at': created_activity.started_at.isoformat()
        }
        self.session_repo.update(session)

        self._publish_log(f"Actividad iniciada: {title}", "error")

        return {'status': 'activity_started'}

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)