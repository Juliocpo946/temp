from typing import Optional
from datetime import datetime

class TokenDTO:
    def __init__(self, id: Optional[int], token: str, company_id: int, created_at: Optional[datetime] = None, expires_at: Optional[datetime] = None, is_active: bool = True):
        self.id = id
        self.token = token
        self.company_id = company_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.is_active = is_active

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'token': self.token,
            'company_id': self.company_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        }
