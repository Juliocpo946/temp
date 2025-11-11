from datetime import datetime
import uuid
from src.domain.entities.token import Token
from src.domain.repositories.application_repository import ApplicationRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.token_repository import TokenRepository
from src.domain.value_objects.token_value import TokenValue
from src.domain.value_objects.api_key_prefix import ApiKeyPrefix
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class GenerateNewApiKeyUseCase:
    def __init__(self, application_repo: ApplicationRepository, company_repo: CompanyRepository, token_repo: TokenRepository, rabbitmq_client: RabbitMQClient):
        self.application_repo = application_repo
        self.company_repo = company_repo
        self.token_repo = token_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, application_id: str) -> dict:
        application = self.application_repo.get_by_id(application_id)
        if not application:
            self._publish_log(f"Intento de generar key para aplicacion inexistente: {application_id}", "error")
            raise ValueError(f"Aplicacion {application_id} no existe")

        if not application.is_active:
            self._publish_log(f"Intento de generar key para aplicacion inactiva: {application_id}", "error")
            raise ValueError(f"Aplicacion {application_id} esta inactiva")

        company = self.company_repo.get_by_id(str(application.company_id))
        if not company or not company.is_active:
            self._publish_log(f"Empresa inactiva o inexistente: {application.company_id}", "error")
            raise ValueError(f"Empresa esta inactiva")

        prefix = ApiKeyPrefix.generate(application.platform, application.environment)
        token_value_obj = TokenValue()
        key_value = f"{prefix}{str(token_value_obj)}"

        token = Token(
            id=None,
            token=key_value,
            company_id=application.company_id,
            created_at=datetime.utcnow(),
            expires_at=None,
            last_used=None,
            is_active=True
        )

        created_token = self.token_repo.create(token)

        self._publish_log(f"Nueva API key generada para aplicacion: {application_id}", "info")
        self._send_generation_email(company, application, created_token)

        return {'api_key': created_token.token}

    def _send_generation_email(self, company, application, token):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Nueva API Key generada</h1>
            <p><strong>Aplicacion:</strong> {application.name}</p>
            <p><strong>Plataforma:</strong> {application.platform}</p>
            <p><strong>Ambiente:</strong> {application.environment}</p>
            <p><strong>Nueva API Key:</strong> {token.token}</p>
            <br>
            <p><strong>Recomendacion:</strong> Actualiza tu aplicacion con la nueva key. Las keys anteriores seguiran funcionando hasta que las revoques manualmente.</p>
          </body>
        </html>
        """
        
        self.rabbitmq_client.publish('emails', {
            'to_email': company.email,
            'subject': 'Nueva API Key generada',
            'html_body': html_body
        })

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)