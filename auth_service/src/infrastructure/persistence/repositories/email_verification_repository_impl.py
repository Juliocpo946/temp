from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.domain.entities.email_verification import EmailVerification
from src.domain.repositories.email_verification_repository import EmailVerificationRepository
from src.infrastructure.persistence.models.email_verification_model import EmailVerificationModel

class EmailVerificationRepositoryImpl(EmailVerificationRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, email_verification: EmailVerification) -> EmailVerification:
        db_verification = EmailVerificationModel(
            email=email_verification.email,
            verification_code=email_verification.verification_code,
            expires_at=email_verification.expires_at,
            is_used=email_verification.is_used
        )
        self.db.add(db_verification)
        self.db.commit()
        self.db.refresh(db_verification)
        return self._to_domain(db_verification)

    def get_by_code(self, verification_code: str) -> Optional[EmailVerification]:
        db_verification = self.db.query(EmailVerificationModel).filter(
            EmailVerificationModel.verification_code == verification_code
        ).first()
        return self._to_domain(db_verification) if db_verification else None

    def get_by_email(self, email: str) -> Optional[EmailVerification]:
        db_verification = self.db.query(EmailVerificationModel).filter(
            EmailVerificationModel.email == email
        ).order_by(EmailVerificationModel.created_at.desc()).first()
        return self._to_domain(db_verification) if db_verification else None

    def update(self, email_verification: EmailVerification) -> EmailVerification:
        db_verification = self.db.query(EmailVerificationModel).filter(
            EmailVerificationModel.id == email_verification.id
        ).first()
        if db_verification:
            db_verification.is_used = email_verification.is_used
            self.db.commit()
            self.db.refresh(db_verification)
            return self._to_domain(db_verification)
        return email_verification

    def invalidate_previous_codes(self, email: str) -> int:
        result = self.db.query(EmailVerificationModel).filter(
            EmailVerificationModel.email == email,
            EmailVerificationModel.is_used == False
        ).update({EmailVerificationModel.is_used: True})
        self.db.commit()
        return result

    def delete_expired(self) -> int:
        result = self.db.query(EmailVerificationModel).filter(
            EmailVerificationModel.expires_at < datetime.utcnow()
        ).delete()
        self.db.commit()
        return result

    def count_recent_attempts(self, email: str, minutes: int) -> int:
        time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
        return self.db.query(EmailVerificationModel).filter(
            EmailVerificationModel.email == email,
            EmailVerificationModel.created_at > time_threshold
        ).count()

    @staticmethod
    def _to_domain(db_verification: EmailVerificationModel) -> EmailVerification:
        return EmailVerification(
            id=db_verification.id,
            email=db_verification.email,
            verification_code=db_verification.verification_code,
            created_at=db_verification.created_at,
            expires_at=db_verification.expires_at,
            is_used=db_verification.is_used
        )