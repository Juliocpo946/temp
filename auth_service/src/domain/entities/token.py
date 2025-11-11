from datetime import datetime
from typing import Optional

class Token:
    def __init__(self, id: int, token: str, company_id: int, created_at: datetime, expires_at: Optional[datetime], last_used: Optional[datetime], is_active: bool):
        self.id = id
        self.token = token
        self.company_id = company_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_used = last_used
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
        self.last_used = datetime.utcnow()
