from datetime import datetime, timedelta
import secrets
import uuid
from src.domain.entities.revocation_token import RevocationToken
from src.domain.repositories.token_repository import TokenRepository
from src.domain.repositories.application_repository import ApplicationRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.revocation_token_repository import RevocationTokenRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class RequestRevokeApiKeyUseCase:
    def __init__(self, token_repo: TokenRepository, application_repo: ApplicationRepository, company_repo: CompanyRepository, revocation_token_repo: RevocationTokenRepository, rabbitmq_client: RabbitMQClient):
        self.token_repo = token_repo
        self.application_repo = application_repo
        self.company_repo = company_repo
        self.revocation_token_repo = revocation_token_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, api_key_id: str) -> dict:
        token = self.token_repo.get_by_id(api_key_id)
        if not token:
            self._publish_log(f"Intento de solicitar revocacion de key inexistente: {api_key_id}", "error")
            raise ValueError("API key no existe")

        company = self.company_repo.get_by_id(str(token.company_id))
        if not company:
            self._publish_log(f"Empresa inexistente para token: {api_key_id}", "error")
            raise ValueError("Empresa no existe")

        confirmation_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        revocation_token = RevocationToken(
            id=None,
            api_key_id=uuid.UUID(api_key_id),
            confirmation_code=confirmation_code,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            is_used=False
        )

        self.revocation_token_repo.create(revocation_token)

        self._send_confirmation_email(company, token, confirmation_code)
        self._publish_log(f"Codigo de revocacion generado para key: {api_key_id}", "info")

        return {
            'message': 'Codigo de confirmacion enviado a tu email',
            'expires_in': 300
        }

    def _send_confirmation_email(self, company, token, code):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Confirma la revocacion de API Key</h1>
            <p>Has solicitado revocar una API key.</p>
            <p><strong>Key:</strong> {token.token[:30]}...</p>
            <br>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center;">
              <h2 style="color: #333; font-size: 32px; letter-spacing: 5px;">{code}</h2>
            </div>
            <br>
            <p>Este codigo expira en 5 minutos.</p>
            <p>Si no solicitaste esta revocacion, ignora este mensaje.</p>
          </body>
        </html>
        """
        
        self.rabbitmq_client.publish('emails', {
            'to_email': company.email,
            'subject': 'Confirma revocacion de API Key',
            'html_body': html_body
        })

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)