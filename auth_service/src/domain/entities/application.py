from datetime import datetime
from typing import Optional
import uuid

class Application:
    def __init__(self, id: Optional[uuid.UUID], company_id: uuid.UUID, name: str, platform: str, environment: str, is_active: bool, created_at: datetime):
        self.id = id or uuid.uuid4()
        self.company_id = company_id
        self.name = name
        self.platform = platform
        self.environment = environment
        self.is_active = is_active
        self.created_at = created_at

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True