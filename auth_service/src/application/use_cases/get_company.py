from src.domain.repositories.company_repository import CompanyRepository
from src.application.dtos.company_dto import CompanyDTO
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class GetCompanyUseCase:
    def __init__(self, company_repo: CompanyRepository, rabbitmq_client: RabbitMQClient):
        self.company_repo = company_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, company_id: int) -> dict:
        company = self.company_repo.get_by_id(company_id)
        if not company:
            self._publish_log(f"Intento de obtener empresa inexistente: {company_id}", "error")
            raise ValueError(f"Empresa {company_id} no existe")

        company_dto = CompanyDTO(
            company.id,
            company.name,
            company.email,
            company.is_active,
            company.created_at,
            company.updated_at
        )

        return company_dto.to_dict()

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)
