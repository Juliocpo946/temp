from datetime import datetime
from typing import Optional
import uuid

class LoginAttempt:
    def __init__(self, id: Optional[uuid.UUID], email: str, otp_code: str, created_at: datetime, expires_at: datetime, is_used: bool):
        self.id = id or uuid.uuid4()
        self.email = email
        self.otp_code = otp_code
        self.created_at = created_at
        self.expires_at = expires_at
        self.is_used = is_used

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def mark_as_used(self) -> None:
        self.is_used = True