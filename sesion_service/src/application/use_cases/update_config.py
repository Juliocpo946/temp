from src.domain.repositories.analysis_config_repository import AnalysisConfigRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import LOG_SERVICE_QUEUE

class UpdateConfigUseCase:
    def __init__(
        self,
        config_repo: AnalysisConfigRepository,
        rabbitmq_client: RabbitMQClient
    ):
        self.config_repo = config_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(
        self,
        session_id: str,
        cognitive_analysis_enabled: bool,
        text_notifications: bool,
        video_suggestions: bool,
        vibration_alerts: bool,
        pause_suggestions: bool
    ) -> dict:
        config = self.config_repo.get_by_session_id(session_id)
        if not config:
            self._publish_log(f"Configuracion no encontrada para sesion: {session_id}", "error")
            raise ValueError("Configuracion no encontrada")

        config.update(
            cognitive_analysis_enabled,
            text_notifications,
            video_suggestions,
            vibration_alerts,
            pause_suggestions
        )
        self.config_repo.update(config)

        self._publish_log(f"Configuracion actualizada para sesion: {session_id}")

        return {'status': 'ok'}

    def _publish_log(self, message: str, level: str = "info") -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)