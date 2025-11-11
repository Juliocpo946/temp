from datetime import datetime
from src.domain.entities.token import Token
from src.domain.repositories.token_repository import TokenRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.value_objects.token_value import TokenValue
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class GenerateTokenUseCase:
    def __init__(self, token_repo: TokenRepository, company_repo: CompanyRepository, rabbitmq_client: RabbitMQClient):
        self.token_repo = token_repo
        self.company_repo = company_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, company_id: int) -> dict:
        company = self.company_repo.get_by_id(company_id)
        if not company:
            self._publish_log(f"Intento de generar token para empresa inexistente: {company_id}", "error")
            raise ValueError(f"Empresa {company_id} no existe")

        if not company.is_active:
            self._publish_log(f"Intento de generar token para empresa inactiva: {company_id}", "error")
            raise ValueError(f"Empresa {company_id} está inactiva")

        token_value = TokenValue()
        token = Token(
            id=None,
            token=str(token_value),
            company_id=company_id,
            created_at=datetime.utcnow(),
            expires_at=None,
            last_used=None,
            is_active=True
        )

        created_token = self.token_repo.create(token)
        self._publish_log(f"Token generado para empresa: {company_id}", "info")

        return {'token': created_token.token}

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)
