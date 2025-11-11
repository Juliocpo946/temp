from typing import Optional
from sqlalchemy.orm import Session
import uuid
from src.domain.entities.revocation_token import RevocationToken
from src.domain.repositories.revocation_token_repository import RevocationTokenRepository
from src.infrastructure.persistence.models.revocation_token_model import RevocationTokenModel

class RevocationTokenRepositoryImpl(RevocationTokenRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, revocation_token: RevocationToken) -> RevocationToken:
        db_revocation_token = RevocationTokenModel(
            api_key_id=revocation_token.api_key_id,
            confirmation_code=revocation_token.confirmation_code,
            expires_at=revocation_token.expires_at,
            is_used=revocation_token.is_used
        )
        self.db.add(db_revocation_token)
        self.db.commit()
        self.db.refresh(db_revocation_token)
        return self._to_domain(db_revocation_token)

    def get_by_code(self, confirmation_code: str) -> Optional[RevocationToken]:
        db_revocation_token = self.db.query(RevocationTokenModel).filter(RevocationTokenModel.confirmation_code == confirmation_code).first()
        return self._to_domain(db_revocation_token) if db_revocation_token else None

    def get_by_api_key_id(self, api_key_id: str) -> Optional[RevocationToken]:
        db_revocation_token = self.db.query(RevocationTokenModel).filter(RevocationTokenModel.api_key_id == uuid.UUID(api_key_id)).first()
        return self._to_domain(db_revocation_token) if db_revocation_token else None

    def update(self, revocation_token: RevocationToken) -> RevocationToken:
        db_revocation_token = self.db.query(RevocationTokenModel).filter(RevocationTokenModel.id == revocation_token.id).first()
        if db_revocation_token:
            db_revocation_token.is_used = revocation_token.is_used
            self.db.commit()
            self.db.refresh(db_revocation_token)
            return self._to_domain(db_revocation_token)
        return revocation_token

    @staticmethod
    def _to_domain(db_revocation_token: RevocationTokenModel) -> RevocationToken:
        return RevocationToken(
            id=db_revocation_token.id,
            api_key_id=db_revocation_token.api_key_id,
            confirmation_code=db_revocation_token.confirmation_code,
            created_at=db_revocation_token.created_at,
            expires_at=db_revocation_token.expires_at,
            is_used=db_revocation_token.is_used
        )