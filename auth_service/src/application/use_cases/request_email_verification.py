from datetime import datetime, timedelta
import secrets
from src.domain.entities.email_verification import EmailVerification
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.email_verification_repository import EmailVerificationRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import (
    MAX_EMAIL_VERIFICATION_ATTEMPTS_PER_HOUR,
    EMAIL_VERIFICATION_CODE_EXPIRATION_MINUTES,
    EMAIL_VERIFICATION_RATE_LIMIT_WINDOW_MINUTES
)

class RequestEmailVerificationUseCase:
    def __init__(self, company_repo: CompanyRepository, email_verification_repo: EmailVerificationRepository, rabbitmq_client: RabbitMQClient):
        self.company_repo = company_repo
        self.email_verification_repo = email_verification_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, name: str, email: str) -> dict:
        existing_company = self.company_repo.get_by_email(email)
        if existing_company:
            raise ValueError(f"Email {email} ya esta registrado")

        recent_attempts = self.email_verification_repo.count_recent_attempts(
            email, 
            EMAIL_VERIFICATION_RATE_LIMIT_WINDOW_MINUTES
        )
        if recent_attempts >= MAX_EMAIL_VERIFICATION_ATTEMPTS_PER_HOUR:
            raise ValueError(f"Demasiados intentos. Intenta nuevamente en {EMAIL_VERIFICATION_RATE_LIMIT_WINDOW_MINUTES} minutos")

        self.email_verification_repo.invalidate_previous_codes(email)
        self.email_verification_repo.delete_expired()

        verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        email_verification = EmailVerification(
            id=None,
            email=email,
            verification_code=verification_code,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=EMAIL_VERIFICATION_CODE_EXPIRATION_MINUTES),
            is_used=False
        )

        self.email_verification_repo.create(email_verification)
        self._send_verification_email(name, email, verification_code)

        return {
            'message': 'Codigo de verificacion enviado a tu email',
            'expires_in': EMAIL_VERIFICATION_CODE_EXPIRATION_MINUTES * 60
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
            <p>Este codigo expira en {EMAIL_VERIFICATION_CODE_EXPIRATION_MINUTES} minutos.</p>
            <p>Si no solicitaste este registro, ignora este mensaje.</p>
          </body>
        </html>
        """
        
        self.rabbitmq_client.publish('emails', {
            'to_email': email,
            'subject': 'Verifica tu correo electronico',
            'html_body': html_body
        })