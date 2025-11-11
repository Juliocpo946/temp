from datetime import datetime
from typing import Optional
import uuid

class RevocationApiKey:
    def __init__(self, id: Optional[uuid.UUID], api_key_id: uuid.UUID, confirmation_code: str, created_at: datetime, expires_at: datetime, is_used: bool):
        self.id = id or uuid.uuid4()
        self.api_key_id = api_key_id
        self.confirmation_code = confirmation_code
        self.created_at = created_at
        self.expires_at = expires_at
        self.is_used = is_used

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def mark_as_used(self) -> None:
        self.is_used = True