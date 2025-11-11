from datetime import datetime
from typing import Optional
import uuid

class ApiKey:
    def __init__(self, id: Optional[uuid.UUID], key_value: str, company_id: uuid.UUID, application_id: uuid.UUID, created_at: datetime, expires_at: Optional[datetime], last_used_at: Optional[datetime], is_active: bool):
        self.id = id or uuid.uuid4()
        self.key_value = key_value
        self.company_id = company_id
        self.application_id = application_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_used_at = last_used_at
        self.is_active = is_active

    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def revoke(self) -> None:
        self.is_active = False

    def update_last_used(self) -> None:
        self.last_used_at = datetime.utcnow()