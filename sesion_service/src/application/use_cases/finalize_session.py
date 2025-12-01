from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.activity_log_repository import ActivityLogRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.activity_event_publisher import ActivityEventPublisher
from src.infrastructure.config.settings import LOG_SERVICE_QUEUE

class FinalizeSessionUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        activity_log_repo: ActivityLogRepository,
        rabbitmq_client: RabbitMQClient
    ):
        self.session_repo = session_repo
        self.activity_log_repo = activity_log_repo
        self.rabbitmq_client = rabbitmq_client
        self.event_publisher = ActivityEventPublisher(rabbitmq_client)

    def execute(self, session_id: str) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            self._publish_log(f"Sesion no encontrada: {session_id}", "error")
            raise ValueError("Sesion no encontrada")

        in_progress = self.activity_log_repo.get_in_progress_by_session(session_id)
        if in_progress:
            in_progress.abandon()
            self.activity_log_repo.update(in_progress)
            self.event_publisher.publish_activity_abandoned(
                str(in_progress.activity_uuid),
                session_id
            )

        session.finalize()
        updated_session = self.session_repo.update(session)

        self._publish_log(f"Sesion finalizada: {session_id}")

        return {
            'status': 'finalizada',
            'ended_at': updated_session.ended_at.isoformat()
        }

    def _publish_log(self, message: str, level: str = "info") -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)