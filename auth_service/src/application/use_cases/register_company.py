from datetime import datetime
from src.domain.entities.company import Company
from src.domain.entities.api_key import ApiKey
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.domain.value_objects.api_key_value import ApiKeyValue
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.dtos.company_dto import CompanyDTO

class RegisterCompanyUseCase:
    def __init__(self, company_repo: CompanyRepository, api_key_repo: ApiKeyRepository, rabbitmq_client: RabbitMQClient):
        self.company_repo = company_repo
        self.api_key_repo = api_key_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, name: str, email: str) -> dict:
        existing_company = self.company_repo.get_by_email(email)
        if existing_company:
            self._publish_log(f"Intento de registro con email duplicado: {email}", "error")
            raise ValueError(f"Email {email} ya esta registrado")

        company = Company(
            id=None,
            name=name,
            email=email,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        created_company = self.company_repo.create(company)

        self._publish_log(f"Empresa registrada: {created_company.email}", "info")

        return {
            'company': CompanyDTO(
                str(created_company.id),
                created_company.name,
                created_company.email,
                created_company.is_active,
                created_company.created_at,
                created_company.updated_at
            ).to_dict()
        }

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)