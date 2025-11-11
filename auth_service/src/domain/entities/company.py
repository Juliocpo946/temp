from datetime import datetime
from typing import Optional

class Company:
    def __init__(self, id: int, name: str, email: str, is_active: bool, created_at: datetime, updated_at: datetime):
        self.id = id
        self.name = name
        self.email = email
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def update(self, name: Optional[str] = None, email: Optional[str] = None) -> None:
        if name:
            self.name = name
        if email:
            self.email = email
        self.updated_at = datetime.utcnow()
