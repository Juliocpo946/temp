from datetime import datetime
from src.domain.entities.company import Company
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.domain.repositories.email_verification_repository import EmailVerificationRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.dtos.company_dto import CompanyDTO

class ConfirmEmailVerificationUseCase:
    def __init__(self, company_repo: CompanyRepository, api_key_repo: ApiKeyRepository, email_verification_repo: EmailVerificationRepository, rabbitmq_client: RabbitMQClient):
        self.company_repo = company_repo
        self.api_key_repo = api_key_repo
        self.email_verification_repo = email_verification_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, name: str, email: str, verification_code: str) -> dict:
        email_verification = self.email_verification_repo.get_by_code(verification_code)
        
        if not email_verification:
            self._publish_log(f"Codigo de verificacion invalido", "error")
            raise ValueError("Codigo de verificacion invalido")

        if email_verification.email != email:
            self._publish_log(f"Email no corresponde al codigo", "error")
            raise ValueError("Email no corresponde al codigo de verificacion")

        if email_verification.is_expired():
            self._publish_log(f"Codigo de verificacion expirado", "error")
            raise ValueError("Codigo de verificacion expirado")

        if email_verification.is_used:
            self._publish_log(f"Codigo ya fue utilizado", "error")
            raise ValueError("Codigo ya fue utilizado")

        existing_company = self.company_repo.get_by_email(email)
        if existing_company:
            self._publish_log(f"Email ya registrado: {email}", "error")
            raise ValueError(f"Email {email} ya esta registrado")

        company = Company(
            id=None,
            name=name,
            email=email,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        created_company = self.company_repo.create(company)

        email_verification.mark_as_used()
        self.email_verification_repo.update(email_verification)

        self._publish_log(f"Empresa registrada: {created_company.email}", "info")
        self._send_welcome_email(created_company)

        return {
            'company': CompanyDTO(
                str(created_company.id),
                created_company.name,
                created_company.email,
                created_company.is_active,
                created_company.created_at,
                created_company.updated_at
            ).to_dict()
        }

    def _send_welcome_email(self, company):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Bienvenido a nuestra plataforma</h1>
            <p>Hola <strong>{company.name}</strong>,</p>
            <p>Tu empresa ha sido registrada exitosamente en nuestra plataforma.</p>
            <p><strong>Email registrado:</strong> {company.email}</p>
            <br>
            <p>Ahora puedes crear aplicaciones y generar API keys para integrar nuestros servicios.</p>
            <p>Gracias por unirte a nosotros.</p>
          </body>
        </html>
        """
        
        self.rabbitmq_client.publish('emails', {
            'to_email': company.email,
            'subject': 'Bienvenido - Registro exitoso',
            'html_body': html_body
        })

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)