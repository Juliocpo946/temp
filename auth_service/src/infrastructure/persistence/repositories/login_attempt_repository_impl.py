from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.domain.entities.login_attempt import LoginAttempt
from src.domain.repositories.login_attempt_repository import LoginAttemptRepository
from src.infrastructure.persistence.models.login_attempt_model import LoginAttemptModel

class LoginAttemptRepositoryImpl(LoginAttemptRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, login_attempt: LoginAttempt) -> LoginAttempt:
        db_login_attempt = LoginAttemptModel(
            email=login_attempt.email,
            otp_code=login_attempt.otp_code,
            expires_at=login_attempt.expires_at,
            is_used=login_attempt.is_used
        )
        self.db.add(db_login_attempt)
        self.db.commit()
        self.db.refresh(db_login_attempt)
        return self._to_domain(db_login_attempt)

    def get_by_code(self, otp_code: str) -> Optional[LoginAttempt]:
        db_login_attempt = self.db.query(LoginAttemptModel).filter(
            LoginAttemptModel.otp_code == otp_code
        ).first()
        return self._to_domain(db_login_attempt) if db_login_attempt else None

    def get_by_email(self, email: str) -> Optional[LoginAttempt]:
        db_login_attempt = self.db.query(LoginAttemptModel).filter(
            LoginAttemptModel.email == email
        ).order_by(LoginAttemptModel.created_at.desc()).first()
        return self._to_domain(db_login_attempt) if db_login_attempt else None

    def update(self, login_attempt: LoginAttempt) -> LoginAttempt:
        db_login_attempt = self.db.query(LoginAttemptModel).filter(
            LoginAttemptModel.id == login_attempt.id
        ).first()
        if db_login_attempt:
            db_login_attempt.is_used = login_attempt.is_used
            self.db.commit()
            self.db.refresh(db_login_attempt)
            return self._to_domain(db_login_attempt)
        return login_attempt

    def invalidate_previous_codes(self, email: str) -> int:
        result = self.db.query(LoginAttemptModel).filter(
            LoginAttemptModel.email == email,
            LoginAttemptModel.is_used == False
        ).update({LoginAttemptModel.is_used: True})
        self.db.commit()
        return result

    def delete_expired(self) -> int:
        result = self.db.query(LoginAttemptModel).filter(
            LoginAttemptModel.expires_at < datetime.utcnow()
        ).delete()
        self.db.commit()
        return result

    def count_recent_attempts(self, email: str, minutes: int) -> int:
        time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
        return self.db.query(LoginAttemptModel).filter(
            LoginAttemptModel.email == email,
            LoginAttemptModel.created_at > time_threshold
        ).count()

    @staticmethod
    def _to_domain(db_login_attempt: LoginAttemptModel) -> LoginAttempt:
        return LoginAttempt(
            id=db_login_attempt.id,
            email=db_login_attempt.email,
            otp_code=db_login_attempt.otp_code,
            created_at=db_login_attempt.created_at,
            expires_at=db_login_attempt.expires_at,
            is_used=db_login_attempt.is_used
        )