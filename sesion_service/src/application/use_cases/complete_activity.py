from src.domain.repositories.activity_log_repository import ActivityLogRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.activity_event_publisher import ActivityEventPublisher
from src.infrastructure.config.settings import LOG_SERVICE_QUEUE

class CompleteActivityUseCase:
    def __init__(
        self,
        activity_log_repo: ActivityLogRepository,
        rabbitmq_client: RabbitMQClient
    ):
        self.activity_log_repo = activity_log_repo
        self.rabbitmq_client = rabbitmq_client
        self.event_publisher = ActivityEventPublisher(rabbitmq_client)

    def execute(self, activity_uuid: str, feedback: dict) -> dict:
        activity = self.activity_log_repo.get_by_uuid(activity_uuid)
        if not activity:
            self._publish_log(f"Actividad no encontrada: {activity_uuid}", "error")
            raise ValueError("Actividad no encontrada")

        if activity.status not in ["en_progreso", "pausada"]:
            self._publish_log(f"Actividad no puede completarse: {activity_uuid} (estado: {activity.status})", "error")
            raise ValueError(f"La actividad no puede completarse, estado actual: {activity.status}")

        activity.complete(feedback)
        self.activity_log_repo.update(activity)

        self.event_publisher.publish_activity_completed(
            activity_uuid,
            str(activity.session_id)
        )

        self._publish_log(f"Actividad completada: {activity_uuid}")

        return {
            'status': 'completada',
            'activity_uuid': activity_uuid,
            'completed_at': activity.completed_at.isoformat()
        }

    def _publish_log(self, message: str, level: str = "info") -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)