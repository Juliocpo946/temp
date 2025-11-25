from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from src.domain.entities.revocation_api_key import RevocationApiKey
from src.domain.repositories.revocation_api_key_repository import RevocationApiKeyRepository
from src.infrastructure.persistence.models.revocation_api_key_model import RevocationApiKeyModel

class RevocationApiKeyRepositoryImpl(RevocationApiKeyRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, revocation_api_key: RevocationApiKey) -> RevocationApiKey:
        db_revocation_api_key = RevocationApiKeyModel(
            api_key_id=revocation_api_key.api_key_id,
            confirmation_code=revocation_api_key.confirmation_code,
            expires_at=revocation_api_key.expires_at,
            is_used=revocation_api_key.is_used
        )
        self.db.add(db_revocation_api_key)
        self.db.commit()
        self.db.refresh(db_revocation_api_key)
        return self._to_domain(db_revocation_api_key)

    def get_by_code(self, confirmation_code: str) -> Optional[RevocationApiKey]:
        db_revocation_api_key = self.db.query(RevocationApiKeyModel).filter(RevocationApiKeyModel.confirmation_code == confirmation_code).first()
        return self._to_domain(db_revocation_api_key) if db_revocation_api_key else None

    def get_by_api_key_id(self, api_key_id: str) -> Optional[RevocationApiKey]:
        db_revocation_api_key = self.db.query(RevocationApiKeyModel).filter(RevocationApiKeyModel.api_key_id == uuid.UUID(api_key_id)).first()
        return self._to_domain(db_revocation_api_key) if db_revocation_api_key else None

    def update(self, revocation_api_key: RevocationApiKey) -> RevocationApiKey:
        db_revocation_api_key = self.db.query(RevocationApiKeyModel).filter(RevocationApiKeyModel.id == revocation_api_key.id).first()
        if db_revocation_api_key:
            db_revocation_api_key.is_used = revocation_api_key.is_used
            self.db.commit()
            self.db.refresh(db_revocation_api_key)
            return self._to_domain(db_revocation_api_key)
        return revocation_api_key

    def invalidate_previous_codes(self, api_key_id: str) -> int:
        result = self.db.query(RevocationApiKeyModel).filter(
            RevocationApiKeyModel.api_key_id == uuid.UUID(api_key_id),
            RevocationApiKeyModel.is_used == False
        ).update({RevocationApiKeyModel.is_used: True})
        self.db.commit()
        return result

    def delete_expired(self) -> int:
        result = self.db.query(RevocationApiKeyModel).filter(
            RevocationApiKeyModel.expires_at < datetime.utcnow()
        ).delete()
        self.db.commit()
        return result

    def count_recent_attempts(self, api_key_id: str, minutes: int) -> int:
        time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
        return self.db.query(RevocationApiKeyModel).filter(
            RevocationApiKeyModel.api_key_id == uuid.UUID(api_key_id),
            RevocationApiKeyModel.created_at > time_threshold
        ).count()

    @staticmethod
    def _to_domain(db_revocation_api_key: RevocationApiKeyModel) -> RevocationApiKey:
        return RevocationApiKey(
            id=db_revocation_api_key.id,
            api_key_id=db_revocation_api_key.api_key_id,
            confirmation_code=db_revocation_api_key.confirmation_code,
            created_at=db_revocation_api_key.created_at,
            expires_at=db_revocation_api_key.expires_at,
            is_used=db_revocation_api_key.is_used
        )