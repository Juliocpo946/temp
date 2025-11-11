from src.domain.repositories.token_repository import TokenRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class ValidateTokenUseCase:
    def __init__(self, token_repo: TokenRepository, company_repo: CompanyRepository, rabbitmq_client: RabbitMQClient):
        self.token_repo = token_repo
        self.company_repo = company_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, token_value: str) -> dict:
        token = self.token_repo.get_by_token(token_value)

        if not token:
            self._publish_log(f"Intento de validación con token inexistente", "error")
            return {'valid': False, 'company_id': None}

        company = self.company_repo.get_by_id(token.company_id)
        if not company or not company.is_active:
            self._publish_log(f"Token de empresa inactiva: {token.company_id}", "error")
            return {'valid': False, 'company_id': None}

        if not token.is_valid():
            self._publish_log(f"Token inválido o expirado: {token_value[:10]}...", "error")
            return {'valid': False, 'company_id': None}

        token.update_last_used()
        self.token_repo.update(token)

        return {'valid': True, 'company_id': token.company_id}

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)
