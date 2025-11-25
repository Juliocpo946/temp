from datetime import datetime, timedelta
import secrets
from src.domain.entities.login_attempt import LoginAttempt
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.login_attempt_repository import LoginAttemptRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import (
    MAX_LOGIN_ATTEMPTS_PER_HOUR,
    LOGIN_OTP_EXPIRATION_MINUTES,
    LOGIN_RATE_LIMIT_WINDOW_MINUTES
)

class RequestLoginUseCase:
    def __init__(self, company_repo: CompanyRepository, login_attempt_repo: LoginAttemptRepository, rabbitmq_client: RabbitMQClient):
        self.company_repo = company_repo
        self.login_attempt_repo = login_attempt_repo
        self.rabbitmq_client = rabbitmq_client

    def execute(self, email: str) -> dict:
        company = self.company_repo.get_by_email(email)
        if not company:
            raise ValueError(f"Email {email} no esta registrado")

        if not company.is_active:
            raise ValueError(f"Empresa inactiva")

        recent_attempts = self.login_attempt_repo.count_recent_attempts(
            email, 
            LOGIN_RATE_LIMIT_WINDOW_MINUTES
        )
        if recent_attempts >= MAX_LOGIN_ATTEMPTS_PER_HOUR:
            raise ValueError(f"Demasiados intentos. Intenta nuevamente en {LOGIN_RATE_LIMIT_WINDOW_MINUTES} minutos")

        self.login_attempt_repo.invalidate_previous_codes(email)
        self.login_attempt_repo.delete_expired()

        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        login_attempt = LoginAttempt(
            id=None,
            email=email,
            otp_code=otp_code,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=LOGIN_OTP_EXPIRATION_MINUTES),
            is_used=False
        )

        self.login_attempt_repo.create(login_attempt)
        self._send_otp_email(company.name, email, otp_code)

        return {
            'message': 'Codigo de acceso enviado a tu email',
            'expires_in': LOGIN_OTP_EXPIRATION_MINUTES * 60
        }

    def _send_otp_email(self, name: str, email: str, code: str):
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h1>Codigo de acceso</h1>
            <p>Hola <strong>{name}</strong>,</p>
            <p>Utiliza el siguiente codigo para acceder a tu cuenta:</p>
            <br>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center;">
              <h2 style="color: #333; font-size: 32px; letter-spacing: 5px;">{code}</h2>
            </div>
            <br>
            <p>Este codigo expira en {LOGIN_OTP_EXPIRATION_MINUTES} minutos.</p>
            <p>Si no solicitaste este acceso, ignora este mensaje.</p>
          </body>
        </html>
        """
        
        self.rabbitmq_client.publish('emails', {
            'to_email': email,
            'subject': 'Codigo de acceso',
            'html_body': html_body
        })