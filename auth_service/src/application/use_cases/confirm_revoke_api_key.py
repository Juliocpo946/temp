from src.domain.repositories.token_repository import TokenRepository
from src.domain.repositories.application_repository import ApplicationRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.revocation_token_repository import RevocationTokenRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class ConfirmRevokeApiKeyUseCase:
    def __init__(self, token_repo: TokenRepository, application_repo: ApplicationRepository, company_repo: CompanyRepository, revocation_token_repo: RevocationTokenRepository, rabbitmq_client: RabbitMQClient):
        self.token_repo = token_repo
        self.application_repo = application_repo
        self.company_repo = company_repo
        self.revocation_token_repo = revocation_token_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, api_key_id: str, confirmation_code: str) -> dict:
        revocation_token = self.revocation_token_repo.get_by_code(confirmation_code)
        
        if not revocation_token:
            self._publish_log(f"Codigo de confirmacion invalido", "error")
            raise ValueError("Codigo de confirmacion invalido")

        if str(revocation_token.api_key_id) != api_key_id:
            self._publish_log(f"Codigo no corresponde a la key solicitada", "error")
            raise ValueError("Codigo no corresponde a esta API key")

        if revocation_token.is_expired():
            self._publish_log(f"Codigo de confirmacion expirado", "error")
            raise ValueError("Codigo de confirmacion expirado")

        if revocation_token.is_used:
            self._publish_log(f"Codigo ya fue utilizado", "error")
            raise ValueError("Codigo ya fue utilizado")

        token = self.token_repo.get_by_id(api_key_id)
        if not token:
            raise ValueError("API key no existe")

        company = self.company_repo.get_by_id(str(token.company_id))

        token.revoke()
        self.token_repo.update(token)

        revocation_token.mark_as_used()
        self.revocation_token_repo.update(revocation_token)

        self._publish_cache_invalidation(token.token)
        self._send_revocation_email(company, token)
        self._publish_log(f"API key revocada: {api_key_id}", "info")

        return {'success': True, 'message': 'API key revocada exitosamente'}

    def _publish_cache_invalidation(self, key_value: str):
        self.rabbitmq_client.publish('cache_invalidation', {
            'action': 'delete',
            'key': f"apikey:{key_value}"
        })

    def _send_revocation_email(self, company, token):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>API Key revocada exitosamente</h1>
            <p><strong>Key revocada:</strong> {token.token[:30]}...</p>
            <p>Esta key ya no funcionara en futuras peticiones.</p>
          </body>
        </html>
        """
        
        self.rabbitmq_client.publish('emails', {
            'to_email': company.email,
            'subject': 'API Key revocada exitosamente',
            'html_body': html_body
        })

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)