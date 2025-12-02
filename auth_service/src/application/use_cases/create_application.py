from datetime import datetime
import uuid
from src.domain.entities.application import Application
from src.domain.repositories.application_repository import ApplicationRepository
from src.domain.repositories.company_repository import CompanyRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.dtos.application_dto import ApplicationDTO

class CreateApplicationUseCase:
    def __init__(self, application_repo: ApplicationRepository, company_repo: CompanyRepository, rabbitmq_client: RabbitMQClient):
        self.application_repo = application_repo
        self.company_repo = company_repo
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
            is_active=False,  # Se crea inactiva esperando el pago
            created_at=datetime.utcnow()
        )

        created_application = self.application_repo.create(application)

        self._publish_log(f"Aplicacion creada (Pendiente de Pago): {created_application.name}", "info")

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
            'message': 'Aplicación creada exitosamente. Se requiere realizar el pago para activar la aplicación y generar la API Key.',
            'payment_required': True
        }

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)