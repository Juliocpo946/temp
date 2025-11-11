from typing import Optional
from sqlalchemy.orm import Session
from src.domain.entities.token import Token
from src.domain.repositories.token_repository import TokenRepository
from src.infrastructure.persistence.models.token_model import TokenModel

class TokenRepositoryImpl(TokenRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, token: Token) -> Token:
        db_token = TokenModel(
            token=token.token,
            company_id=token.company_id,
            expires_at=token.expires_at,
            is_active=token.is_active
        )
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        return self._to_domain(db_token)

    def get_by_token(self, token_value: str) -> Optional[Token]:
        db_token = self.db.query(TokenModel).filter(TokenModel.token == token_value).first()
        return self._to_domain(db_token) if db_token else None

    def get_by_company_id(self, company_id: int) -> list[Token]:
        db_tokens = self.db.query(TokenModel).filter(TokenModel.company_id == company_id).all()
        return [self._to_domain(t) for t in db_tokens]

    def update(self, token: Token) -> Token:
        db_token = self.db.query(TokenModel).filter(TokenModel.id == token.id).first()
        if db_token:
            db_token.last_used = token.last_used
            db_token.is_active = token.is_active
            self.db.commit()
            self.db.refresh(db_token)
            return self._to_domain(db_token)
        return token

    def revoke_by_token(self, token_value: str) -> bool:
        db_token = self.db.query(TokenModel).filter(TokenModel.token == token_value).first()
        if db_token:
            db_token.is_active = False
            self.db.commit()
            return True
        return False

    def revoke_all_by_company(self, company_id: int) -> int:
        tokens = self.db.query(TokenModel).filter(TokenModel.company_id == company_id).all()
        for token in tokens:
            token.is_active = False
        self.db.commit()
        return len(tokens)

    @staticmethod
    def _to_domain(db_token: TokenModel) -> Token:
        return Token(
            id=db_token.id,
            token=db_token.token,
            company_id=db_token.company_id,
            created_at=db_token.created_at,
            expires_at=db_token.expires_at,
            last_used=db_token.last_used,
            is_active=db_token.is_active
        )
