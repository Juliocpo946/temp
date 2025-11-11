from src.domain.repositories.application_repository import ApplicationRepository
from src.application.dtos.application_dto import ApplicationDTO
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class GetApplicationUseCase:
    def __init__(self, application_repo: ApplicationRepository, rabbitmq_client: RabbitMQClient):
        self.application_repo = application_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, application_id: str) -> dict:
        application = self.application_repo.get_by_id(application_id)
        if not application:
            self._publish_log(f"Intento de obtener aplicacion inexistente: {application_id}", "error")
            raise ValueError(f"Aplicacion {application_id} no existe")

        application_dto = ApplicationDTO(
            str(application.id),
            str(application.company_id),
            application.name,
            application.platform,
            application.environment,
            application.is_active,
            application.created_at
        )

        return application_dto.to_dict()

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)