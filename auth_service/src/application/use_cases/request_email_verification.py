from datetime import datetime, timedelta
import secrets
from src.domain.entities.email_verification import EmailVerification
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.email_verification_repository import EmailVerificationRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient

class RequestEmailVerificationUseCase:
    def __init__(self, company_repo: CompanyRepository, email_verification_repo: EmailVerificationRepository, rabbitmq_client: RabbitMQClient):
        self.company_repo = company_repo
        self.email_verification_repo = email_verification_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, name: str, email: str) -> dict:
        existing_company = self.company_repo.get_by_email(email)
        if existing_company:
            self._publish_log(f"Intento de registro con email duplicado: {email}", "error")
            raise ValueError(f"Email {email} ya esta registrado")

        verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        email_verification = EmailVerification(
            id=None,
            email=email,
            verification_code=verification_code,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_used=False
        )

        self.email_verification_repo.create(email_verification)

        self._send_verification_email(name, email, verification_code)
        self._publish_log(f"Codigo de verificacion generado para: {email}", "info")

        return {
            'message': 'Codigo de verificacion enviado a tu email',
            'expires_in': 600
        }

    def _send_verification_email(self, name: str, email: str, code: str):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Verifica tu correo electronico</h1>
            <p>Hola <strong>{name}</strong>,</p>
            <p>Para completar tu registro, utiliza el siguiente codigo de verificacion:</p>
            <br>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center;">
              <h2 style="color: #333; font-size: 32px; letter-spacing: 5px;">{code}</h2>
            </div>
            <br>
            <p>Este codigo expira en 10 minutos.</p>
            <p>Si no solicitaste este registro, ignora este mensaje.</p>
          </body>
        </html>
        """
        
        self.rabbitmq_client.publish('emails', {
            'to_email': email,
            'subject': 'Verifica tu correo electronico',
            'html_body': html_body
        })

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'auth-service',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)