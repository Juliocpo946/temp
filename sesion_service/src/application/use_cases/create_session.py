from datetime import datetime
import uuid
from src.domain.entities.session import Session
from src.domain.entities.analysis_config import AnalysisConfig
from src.domain.repositories.session_repository import SessionRepository
from src.domain.repositories.analysis_config_repository import AnalysisConfigRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import LOG_SERVICE_QUEUE

class CreateSessionUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        config_repo: AnalysisConfigRepository,
        rabbitmq_client: RabbitMQClient
    ):
        self.session_repo = session_repo
        self.config_repo = config_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(
        self,
        user_id: int,
        company_id: str,
        disability_type: str,
        cognitive_analysis_enabled: bool
    ) -> dict:
        session = Session(
            id=None,
            user_id=user_id,
            company_id=uuid.UUID(company_id),
            disability_type=disability_type,
            cognitive_analysis_enabled=cognitive_analysis_enabled,
            created_at=datetime.utcnow(),
            ended_at=None
        )

        created_session = self.session_repo.create(session)

        config = AnalysisConfig(
            id=None,
            session_id=created_session.id,
            cognitive_analysis_enabled=cognitive_analysis_enabled,
            text_notifications=True,
            video_suggestions=True,
            vibration_alerts=True,
            pause_suggestions=True
        )
        self.config_repo.create(config)

        self._publish_log(f"Sesion creada: {created_session.id}")

        return {
            'session_id': str(created_session.id),
            'created_at': created_session.created_at.isoformat()
        }

    def _publish_log(self, message: str, level: str = "info") -> None:
        log_message = {
            'service': 'session-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)