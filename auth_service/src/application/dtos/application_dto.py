from typing import Optional
from datetime import datetime

class ApplicationDTO:
    def __init__(self, id: Optional[str], company_id: str, name: str, platform: str, environment: str, is_active: bool, created_at: Optional[datetime] = None):
        self.id = id
        self.company_id = company_id
        self.name = name
        self.platform = platform
        self.environment = environment
        self.is_active = is_active
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'company_id': str(self.company_id),
            'name': self.name,
            'platform': self.platform,
            'environment': self.environment,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }