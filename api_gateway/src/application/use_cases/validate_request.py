from src.infrastructure.http.http_client import HTTPClient
from src.infrastructure.config.settings import AUTH_SERVICE_URL
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class ValidateRequestUseCase:
    def __init__(self, http_client: HTTPClient, rabbitmq_client: RabbitMQClient):
        self.http_client = http_client
        self.rabbitmq_client = rabbitmq_client

    async def execute(self, api_key: str) -> dict:
        try:
            validation_url = f"{AUTH_SERVICE_URL}/auth/api_keys/validate"
            response = await self.http_client.post(
                validation_url,
                json={"api_key": api_key}
            )
            
            if response.get('valid'):
                self._publish_log(f"Api key validado correctamente", "info")
                return {
                    'valid': True,
                    'company_id': response.get('company_id')
                }
            else:
                self._publish_log(f"Api key inválida", "error")
                return {'valid': False, 'company_id': None}
                
        except Exception as e:
            self._publish_log(f"Error al validar api key: {str(e)}", "error")
            return {'valid': False, 'company_id': None}

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'api-gateway',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)