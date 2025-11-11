from datetime import datetime
import uuid
from src.domain.entities.application import Application
from src.domain.entities.token import Token
from src.domain.repositories.application_repository import ApplicationRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.token_repository import TokenRepository
from src.domain.value_objects.token_value import TokenValue
from src.domain.value_objects.api_key_prefix import ApiKeyPrefix
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.dtos.application_dto import ApplicationDTO

class CreateApplicationUseCase:
    def __init__(self, application_repo: ApplicationRepository, company_repo: CompanyRepository, token_repo: TokenRepository, rabbitmq_client: RabbitMQClient):
        self.application_repo = application_repo
        self.company_repo = company_repo
        self.token_repo = token_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, company_id: str, name: str, platform: str, environment: str) -> dict:
        company = self.company_repo.get_by_id(company_id)
        if not company:
            self._publish_log(f"Intento de crear aplicacion para empresa inexistente: {company_id}", "error")
            raise ValueError(f"Empresa {company_id} no existe")

        if not company.is_active:
            self._publish_log(f"Intento de crear aplicacion para empresa inactiva: {company_id}", "error")
            raise ValueError(f"Empresa {company_id} esta inactiva")

        application = Application(
            id=None,
            company_id=uuid.UUID(company_id),
            name=name,
            platform=platform,
            environment=environment,
            is_active=True,
            created_at=datetime.utcnow()
        )

        created_application = self.application_repo.create(application)

        prefix = ApiKeyPrefix.generate(platform, environment)
        token_value_obj = TokenValue()
        key_value = f"{prefix}{str(token_value_obj)}"

        token = Token(
            id=None,
            token=key_value,
            company_id=uuid.UUID(company_id),
            created_at=datetime.utcnow(),
            expires_at=None,
            last_used=None,
            is_active=True
        )

        created_token = self.token_repo.create(token)

        self._publish_log(f"Aplicacion creada: {created_application.name}", "info")
        self._send_creation_email(company, created_application, created_token)

        application_dto = ApplicationDTO(
            str(created_application.id),
            str(created_application.company_id),
            created_application.name,
            created_application.platform,
            created_application.environment,
            created_application.is_active,
            created_application.created_at
        )

        return {
            'application': application_dto.to_dict(),
            'api_key': created_token.token
        }

    def _send_creation_email(self, company, application, token):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Nueva aplicacion creada</h1>
            <p><strong>Nombre:</strong> {application.name}</p>
            <p><strong>Plataforma:</strong> {application.platform}</p>
            <p><strong>Ambiente:</strong> {application.environment}</p>
            <p><strong>API Key:</strong> {token.token}</p>
            <br>
            <p style="color: red;"><strong>IMPORTANTE:</strong> Guarda esta API key de forma segura. No la compartas publicamente.</p>
          </body>
        </html>
        """
        
        self.rabbitmq_client.publish('emails', {
            'to_email': company.email,
            'subject': 'Nueva aplicacion creada exitosamente',
            'html_body': html_body
        })

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)