from typing import Optional, List
from sqlalchemy.orm import Session
import uuid
from src.domain.entities.api_key import ApiKey
from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.infrastructure.persistence.models.api_key_model import ApiKeyModel

class ApiKeyRepositoryImpl(ApiKeyRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, api_key: ApiKey) -> ApiKey:
        db_api_key = ApiKeyModel(
            key_value=api_key.key_value,
            company_id=api_key.company_id,
            application_id=api_key.application_id,
            expires_at=api_key.expires_at,
            is_active=api_key.is_active
        )
        self.db.add(db_api_key)
        self.db.commit()
        self.db.refresh(db_api_key)
        return self._to_domain(db_api_key)

    def get_by_id(self, api_key_id: str) -> Optional[ApiKey]:
        db_api_key = self.db.query(ApiKeyModel).filter(ApiKeyModel.id == uuid.UUID(api_key_id)).first()
        return self._to_domain(db_api_key) if db_api_key else None

    def get_by_key_value(self, key_value: str) -> Optional[ApiKey]:
        db_api_key = self.db.query(ApiKeyModel).filter(ApiKeyModel.key_value == key_value).first()
        return self._to_domain(db_api_key) if db_api_key else None

    def get_by_company_id(self, company_id: str) -> List[ApiKey]:
        db_api_keys = self.db.query(ApiKeyModel).filter(ApiKeyModel.company_id == uuid.UUID(company_id)).all()
        return [self._to_domain(k) for k in db_api_keys]

    def get_by_application_id(self, application_id: str) -> List[ApiKey]:
        db_api_keys = self.db.query(ApiKeyModel).filter(ApiKeyModel.application_id == uuid.UUID(application_id)).all()
        return [self._to_domain(k) for k in db_api_keys]

    def update(self, api_key: ApiKey) -> ApiKey:
        db_api_key = self.db.query(ApiKeyModel).filter(ApiKeyModel.id == api_key.id).first()
        if db_api_key:
            db_api_key.last_used_at = api_key.last_used_at
            db_api_key.is_active = api_key.is_active
            self.db.commit()
            self.db.refresh(db_api_key)
            return self._to_domain(db_api_key)
        return api_key

    def revoke_by_key_value(self, key_value: str) -> bool:
        db_api_key = self.db.query(ApiKeyModel).filter(ApiKeyModel.key_value == key_value).first()
        if db_api_key:
            db_api_key.is_active = False
            self.db.commit()
            return True
        return False

    def revoke_all_by_company(self, company_id: str) -> int:
        api_keys = self.db.query(ApiKeyModel).filter(ApiKeyModel.company_id == uuid.UUID(company_id)).all()
        for api_key in api_keys:
            api_key.is_active = False
        self.db.commit()
        return len(api_keys)

    @staticmethod
    def _to_domain(db_api_key: ApiKeyModel) -> ApiKey:
        return ApiKey(
            id=db_api_key.id,
            key_value=db_api_key.key_value,
            company_id=db_api_key.company_id,
            application_id=db_api_key.application_id,
            created_at=db_api_key.created_at,
            expires_at=db_api_key.expires_at,
            last_used_at=db_api_key.last_used_at,
            is_active=db_api_key.is_active
        )