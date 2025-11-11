from typing import Optional
from src.domain.repositories.company_repository import CompanyRepository
from src.application.dtos.company_dto import CompanyDTO
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class UpdateCompanyUseCase:
    def __init__(self, company_repo: CompanyRepository, rabbitmq_client: RabbitMQClient):
        self.company_repo = company_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, company_id: int, name: Optional[str] = None, email: Optional[str] = None, is_active: Optional[bool] = None) -> dict:
        company = self.company_repo.get_by_id(company_id)
        if not company:
            self._publish_log(f"Intento de actualizar empresa inexistente: {company_id}", "error")
            raise ValueError(f"Empresa {company_id} no existe")

        if email and email != company.email:
            existing = self.company_repo.get_by_email(email)
            if existing:
                self._publish_log(f"Intento de usar email duplicado: {email}", "error")
                raise ValueError(f"Email {email} ya está en uso")

        if name:
            company.name = name
        if email:
            company.email = email
        if is_active is not None:
            if is_active:
                company.activate()
            else:
                company.deactivate()

        updated_company = self.company_repo.update(company)
        self._publish_log(f"Empresa actualizada: {company_id}", "info")

        company_dto = CompanyDTO(
            updated_company.id,
            updated_company.name,
            updated_company.email,
            updated_company.is_active,
            updated_company.created_at,
            updated_company.updated_at
        )

        return company_dto.to_dict()

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)
