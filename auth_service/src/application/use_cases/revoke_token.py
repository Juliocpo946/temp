from src.domain.repositories.token_repository import TokenRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class RevokeTokenUseCase:
    def __init__(self, token_repo: TokenRepository, rabbitmq_client: RabbitMQClient):
        self.token_repo = token_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, token_value: str) -> dict:
        token = self.token_repo.get_by_token(token_value)
        if not token:
            self._publish_log(f"Intento de revocar token inexistente", "error")
            raise ValueError("Token no existe")

        self.token_repo.revoke_by_token(token_value)
        self._publish_log(f"Token revocado", "info")

        return {'success': True}

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)
