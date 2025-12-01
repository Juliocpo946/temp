from datetime import datetime
import uuid
from src.domain.entities.activity_log import ActivityLog
from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.activity_log_repository import ActivityLogRepository
from src.domain.repositories.external_activity_repository import ExternalActivityRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.activity_event_publisher import ActivityEventPublisher
from src.infrastructure.config.settings import LOG_SERVICE_QUEUE

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
        self.event_publisher = ActivityEventPublisher(rabbitmq_client)

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

        if not session.is_active():
            self._publish_log(f"Sesion finalizada: {session_id}", "error")
            raise ValueError("La sesion ya fue finalizada")

        in_progress = self.activity_log_repo.get_in_progress_by_session(session_id)
        if in_progress:
            self._publish_log(f"Ya existe actividad en progreso: {in_progress.activity_uuid}", "error")
            raise ValueError("Ya existe una actividad en progreso")

        self.external_activity_repo.get_or_create(
            external_activity_id,
            title,
            subtitle,
            content,
            activity_type
        )

        activity_uuid = uuid.uuid4()
        activity_log = ActivityLog(
            id=None,
            activity_uuid=activity_uuid,
            session_id=session.id,
            external_activity_id=external_activity_id,
            status="en_progreso",
            started_at=datetime.utcnow(),
            paused_at=None,
            resumed_at=None,
            completed_at=None,
            feedback_data=None
        )

        created_activity = self.activity_log_repo.create(activity_log)

        self.event_publisher.publish_activity_created(
            str(created_activity.activity_uuid),
            session_id,
            external_activity_id,
            session.user_id
        )

        self._publish_log(f"Actividad iniciada: {title} (uuid: {activity_uuid})")

        return {
            'status': 'activity_started',
            'activity_uuid': str(created_activity.activity_uuid),
            'external_activity_id': external_activity_id,
            'started_at': created_activity.started_at.isoformat()
        }

    def _publish_log(self, message: str, level: str = "info") -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)