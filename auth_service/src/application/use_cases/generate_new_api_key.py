from datetime import datetime
import uuid
from src.domain.entities.api_key import ApiKey
from src.domain.repositories.application_repository import ApplicationRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.domain.value_objects.api_key_value import ApiKeyValue
from src.domain.value_objects.api_key_prefix import ApiKeyPrefix
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.domain.services.hashing_service import HashingService


class GenerateNewApiKeyUseCase:
    def __init__(self, application_repo: ApplicationRepository, company_repo: CompanyRepository,
                 api_key_repo: ApiKeyRepository, rabbitmq_client: RabbitMQClient):
        self.application_repo = application_repo
        self.company_repo = company_repo
        self.api_key_repo = api_key_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, application_id: str) -> dict:

        application = self.application_repo.get_by_id(application_id)
        if not application:
            raise ValueError(f"Aplicacion {application_id} no existe")

        if not application.is_active:
            raise ValueError(f"Aplicacion {application_id} esta inactiva/deshabilitada. No se pueden generar keys.")

        company = self.company_repo.get_by_id(str(application.company_id))
        if not company or not company.is_active:
            raise ValueError(f"Empresa esta inactiva")


        existing_keys = self.api_key_repo.get_by_application_id(application_id)
        for old_key in existing_keys:
            if old_key.is_active:
                old_key.revoke()
                self.api_key_repo.update(old_key)


        prefix = ApiKeyPrefix.generate(application.platform, application.environment)
        api_key_value_obj = ApiKeyValue()
        plain_api_key = f"{prefix}{str(api_key_value_obj)}"

        hashed_api_key = HashingService.hash_api_key(plain_api_key)

        api_key = ApiKey(
            id=None,
            key_value=hashed_api_key,
            company_id=application.company_id,
            application_id=application.id,
            created_at=datetime.utcnow(),
            expires_at=None,
            last_used_at=None,
            is_active=True
        )

        self.api_key_repo.create(api_key)

        self._publish_log(f"Nueva API key generada (anteriores revocadas) para app: {application.name}", "info")

        self._send_generation_email(company, application, plain_api_key)

        return {'api_key': plain_api_key}

    def _send_generation_email(self, company, application, plain_api_key):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Nueva API Key generada</h1>
            <p><strong>Aplicacion:</strong> {application.name}</p>
            <p>Se ha generado una nueva credencial. <strong>Cualquier API Key anterior para esta aplicación ha sido desactivada automáticamente.</strong></p>
            <br>
            <p><strong>Nueva API Key:</strong> {plain_api_key}</p>
          </body>
        </html>
        """

        self.rabbitmq_client.publish('emails', {
            'to_email': company.email,
            'subject': 'Rotación de API Key Exitosa',
            'html_body': html_body
        })

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)