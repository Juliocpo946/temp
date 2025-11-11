from datetime import datetime
from typing import Optional

class EmailEvent:
    def __init__(self, event_type: str, email: str, subject: str, data: dict, created_at: Optional[datetime] = None):
        self.event_type = event_type
        self.email = email
        self.subject = subject
        self.data = data
        self.created_at = created_at or datetime.utcnow()