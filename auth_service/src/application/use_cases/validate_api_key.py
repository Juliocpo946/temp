from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.domain.services.hashing_service import HashingService

class ValidateApiKeyUseCase:
    def __init__(self, api_key_repo: ApiKeyRepository, company_repo: CompanyRepository, rabbitmq_client: RabbitMQClient):
        self.api_key_repo = api_key_repo
        self.company_repo = company_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, key_value: str) -> dict:
        hashed_input_key = HashingService.hash_api_key(key_value)

        api_key = self.api_key_repo.get_by_key_value(hashed_input_key)

        if not api_key:
            self._publish_log(f"Intento de validacion con API key inexistente", "error")
            return {'valid': False, 'company_id': None, 'application_id': None}

        company = self.company_repo.get_by_id(str(api_key.company_id))
        if not company or not company.is_active:
            self._publish_log(f"API key de empresa inactiva: {api_key.company_id}", "error")
            return {'valid': False, 'company_id': None, 'application_id': None}

        if not api_key.is_valid():
            self._publish_log(f"API key invalida o expirada: {key_value[:10]}...", "error")
            return {'valid': False, 'company_id': None, 'application_id': None}

        api_key.update_last_used()
        self.api_key_repo.update(api_key)

        return {
            'valid': True,
            'company_id': str(api_key.company_id),
            'application_id': str(api_key.application_id)
        }

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)