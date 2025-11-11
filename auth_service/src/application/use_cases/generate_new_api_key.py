from datetime import datetime
import uuid
from src.domain.entities.api_key import ApiKey
from src.domain.repositories.application_repository import ApplicationRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.domain.value_objects.api_key_value import ApiKeyValue
from src.domain.value_objects.api_key_prefix import ApiKeyPrefix
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class GenerateNewApiKeyUseCase:
    def __init__(self, application_repo: ApplicationRepository, company_repo: CompanyRepository, api_key_repo: ApiKeyRepository, rabbitmq_client: RabbitMQClient):
        self.application_repo = application_repo
        self.company_repo = company_repo
        self.api_key_repo = api_key_repo
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
        api_key_value_obj = ApiKeyValue()
        key_value = f"{prefix}{str(api_key_value_obj)}"

        api_key = ApiKey(
            id=None,
            key_value=key_value,
            company_id=application.company_id,
            application_id=application.id,
            created_at=datetime.utcnow(),
            expires_at=None,
            last_used_at=None,
            is_active=True
        )

        created_api_key = self.api_key_repo.create(api_key)

        self._publish_log(f"Nueva API key generada para aplicacion: {application_id}", "info")
        self._send_generation_email(company, application, created_api_key)

        return {'api_key': created_api_key.key_value}

    def _send_generation_email(self, company, application, api_key):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Nueva API Key generada</h1>
            <p><strong>Aplicacion:</strong> {application.name}</p>
            <p><strong>Plataforma:</strong> {application.platform}</p>
            <p><strong>Ambiente:</strong> {application.environment}</p>
            <p><strong>Nueva API Key:</strong> {api_key.key_value}</p>
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