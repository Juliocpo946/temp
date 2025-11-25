from datetime import datetime, timedelta
import secrets
import uuid
from src.domain.entities.revocation_api_key import RevocationApiKey
from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.domain.repositories.application_repository import ApplicationRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.revocation_api_key_repository import RevocationApiKeyRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import (
    MAX_REVOCATION_ATTEMPTS_PER_HOUR,
    REVOCATION_CODE_EXPIRATION_MINUTES,
    REVOCATION_RATE_LIMIT_WINDOW_MINUTES
)

class RequestRevokeApiKeyUseCase:
    def __init__(self, api_key_repo: ApiKeyRepository, application_repo: ApplicationRepository, company_repo: CompanyRepository, revocation_api_key_repo: RevocationApiKeyRepository, rabbitmq_client: RabbitMQClient):
        self.api_key_repo = api_key_repo
        self.application_repo = application_repo
        self.company_repo = company_repo
        self.revocation_api_key_repo = revocation_api_key_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, api_key_id: str) -> dict:
        api_key = self.api_key_repo.get_by_id(api_key_id)
        if not api_key:
            raise ValueError("API key no existe")

        if not api_key.is_active:
            raise ValueError("API key ya esta revocada")

        company = self.company_repo.get_by_id(str(api_key.company_id))
        if not company:
            raise ValueError("Empresa no existe")

        recent_attempts = self.revocation_api_key_repo.count_recent_attempts(
            api_key_id, 
            REVOCATION_RATE_LIMIT_WINDOW_MINUTES
        )
        if recent_attempts >= MAX_REVOCATION_ATTEMPTS_PER_HOUR:
            raise ValueError(f"Demasiados intentos. Intenta nuevamente en {REVOCATION_RATE_LIMIT_WINDOW_MINUTES} minutos")

        self.revocation_api_key_repo.invalidate_previous_codes(api_key_id)
        self.revocation_api_key_repo.delete_expired()

        confirmation_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        revocation_api_key = RevocationApiKey(
            id=None,
            api_key_id=uuid.UUID(api_key_id),
            confirmation_code=confirmation_code,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=REVOCATION_CODE_EXPIRATION_MINUTES),
            is_used=False
        )

        self.revocation_api_key_repo.create(revocation_api_key)
        self._send_confirmation_email(company, api_key, confirmation_code)

        return {
            'message': 'Codigo de confirmacion enviado a tu email',
            'expires_in': REVOCATION_CODE_EXPIRATION_MINUTES * 60
        }

    def _send_confirmation_email(self, company, api_key, code):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Confirma la revocacion de API Key</h1>
            <p>Has solicitado revocar una API key.</p>
            <p><strong>Key:</strong> {api_key.key_value[:30]}...</p>
            <br>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center;">
              <h2 style="color: #333; font-size: 32px; letter-spacing: 5px;">{code}</h2>
            </div>
            <br>
            <p>Este codigo expira en {REVOCATION_CODE_EXPIRATION_MINUTES} minutos.</p>
            <p>Si no solicitaste esta revocacion, ignora este mensaje.</p>
          </body>
        </html>
        """
        
        self.rabbitmq_client.publish('emails', {
            'to_email': company.email,
            'subject': 'Confirma revocacion de API Key',
            'html_body': html_body
        })