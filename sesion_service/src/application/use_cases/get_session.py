from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.activity_log_repository import ActivityLogRepository
from src.application.dtos.session_dto import SessionDTO
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import LOG_SERVICE_QUEUE

class GetSessionUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        activity_log_repo: ActivityLogRepository,
        rabbitmq_client: RabbitMQClient
    ):
        self.session_repo = session_repo
        self.activity_log_repo = activity_log_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, session_id: str) -> dict:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            self._publish_log(f"Sesion no encontrada: {session_id}", "error")
            raise ValueError("Sesion no encontrada")

        activities = self.activity_log_repo.get_by_session_id(session_id)
        activities_list = []
        for activity in activities:
            activities_list.append({
                'activity_uuid': str(activity.activity_uuid),
                'external_activity_id': activity.external_activity_id,
                'status': activity.status,
                'started_at': activity.started_at.isoformat()
            })

        current_activity = None
        in_progress = self.activity_log_repo.get_in_progress_by_session(session_id)
        if in_progress:
            current_activity = {
                'activity_uuid': str(in_progress.activity_uuid),
                'external_activity_id': in_progress.external_activity_id,
                'status': in_progress.status,
                'started_at': in_progress.started_at.isoformat()
            }

        return {
            'session_id': str(session.id),
            'user_id': session.user_id,
            'company_id': str(session.company_id),
            'disability_type': session.disability_type,
            'cognitive_analysis_enabled': session.cognitive_analysis_enabled,
            'created_at': session.created_at.isoformat(),
            'ended_at': session.ended_at.isoformat() if session.ended_at else None,
            'is_active': session.is_active(),
            'current_activity': current_activity,
            'activities': activities_list
        }

    def _publish_log(self, message: str, level: str = "info") -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)