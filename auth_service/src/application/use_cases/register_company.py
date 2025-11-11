from datetime import datetime
from src.domain.entities.company import Company
from src.domain.entities.token import Token
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.token_repository import TokenRepository
from src.domain.value_objects.token_value import TokenValue
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.dtos.company_dto import CompanyDTO
from src.application.dtos.token_dto import TokenDTO

class RegisterCompanyUseCase:
    def __init__(self, company_repo: CompanyRepository, token_repo: TokenRepository, rabbitmq_client: RabbitMQClient):
        self.company_repo = company_repo
        self.token_repo = token_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, name: str, email: str) -> dict:
        existing_company = self.company_repo.get_by_email(email)
        if existing_company:
            self._publish_log(f"Intento de registro con email duplicado: {email}", "error")
            raise ValueError(f"Email {email} ya está registrado")

        company = Company(
            id=None,
            name=name,
            email=email,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        created_company = self.company_repo.create(company)

        token_value = TokenValue()
        token = Token(
            id=None,
            token=str(token_value),
            company_id=created_company.id,
            created_at=datetime.utcnow(),
            expires_at=None,
            last_used=None,
            is_active=True
        )

        created_token = self.token_repo.create(token)

        self._publish_log(f"Empresa registrada: {created_company.email}", "info")

        return {
            'company': CompanyDTO(
                created_company.id,
                created_company.name,
                created_company.email,
                created_company.is_active,
                created_company.created_at,
                created_company.updated_at
            ).to_dict(),
            'token': created_token.token
        }

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)
