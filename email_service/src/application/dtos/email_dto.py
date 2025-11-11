from datetime import datetime
from typing import Optional

class EmailDTO:
    def __init__(self, event_type: str, email: str, subject: str, data: dict, created_at: Optional[datetime] = None):
        self.event_type = event_type
        self.email = email
        self.subject = subject
        self.data = data
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            'event_type': self.event_type,
            'email': self.email,
            'subject': self.subject,
            'data': self.data,
            'created_at': self.created_at.isoformat()
        }