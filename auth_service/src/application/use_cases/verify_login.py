from datetime import datetime, timedelta
import jwt
from src.domain.repositories.company_repository import CompanyRepository
from src.domain.repositories.login_attempt_repository import LoginAttemptRepository
from src.infrastructure.config.settings import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from src.application.dtos.company_dto import CompanyDTO

class VerifyLoginUseCase:
    def __init__(self, company_repo: CompanyRepository, login_attempt_repo: LoginAttemptRepository):
        self.company_repo = company_repo
        self.login_attempt_repo = login_attempt_repo

    def execute(self, email: str, otp_code: str) -> dict:
        company = self.company_repo.get_by_email(email)
        if not company:
            raise ValueError(f"Email {email} no esta registrado")

        if not company.is_active:
            raise ValueError(f"Empresa inactiva")

        login_attempt = self.login_attempt_repo.get_by_code(otp_code)
        
        if not login_attempt:
            raise ValueError("Codigo de acceso invalido")

        if login_attempt.email != email:
            raise ValueError("Email no corresponde al codigo de acceso")

        if login_attempt.is_used:
            raise ValueError("Codigo ya fue utilizado")

        if login_attempt.is_expired():
            raise ValueError("Codigo de acceso expirado")

        login_attempt.mark_as_used()
        self.login_attempt_repo.update(login_attempt)
        self.login_attempt_repo.delete_expired()

        token = self._generate_jwt_token(str(company.id), company.email)

        return {
            'token': token,
            'expires_in': JWT_EXPIRATION_HOURS * 3600,
            'company': CompanyDTO(
                str(company.id),
                company.name,
                company.email,
                company.is_active,
                company.created_at,
                company.updated_at
            ).to_dict()
        }

    def _generate_jwt_token(self, company_id: str, email: str) -> str:
        payload = {
            'company_id': company_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)