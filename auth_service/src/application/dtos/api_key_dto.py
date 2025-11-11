from typing import Optional
from datetime import datetime

class ApiKeyDTO:
    def __init__(self, id: Optional[str], key_value: str, company_id: str, application_id: str, created_at: Optional[datetime] = None, expires_at: Optional[datetime] = None, is_active: bool = True):
        self.id = id
        self.key_value = key_value
        self.company_id = company_id
        self.application_id = application_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.is_active = is_active

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'key_value': self.key_value,
            'company_id': str(self.company_id),
            'application_id': str(self.application_id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        }