from src.domain.repositories.application_repository import ApplicationRepository
from src.application.dtos.application_dto import ApplicationDTO
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class GetApplicationsUseCase:
    def __init__(self, application_repo: ApplicationRepository, rabbitmq_client: RabbitMQClient):
        self.application_repo = application_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, company_id: str) -> dict:
        applications = self.application_repo.get_by_company_id(company_id)
        
        applications_dtos = [
            ApplicationDTO(
                str(app.id),
                str(app.company_id),
                app.name,
                app.platform,
                app.environment,
                app.is_active,
                app.created_at
            ).to_dict()
            for app in applications
        ]

        return {
            'applications': applications_dtos,
            'total': len(applications_dtos)
        }