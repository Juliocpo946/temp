from datetime import datetime
from typing import Optional

class LogDTO:
    def __init__(self, id: Optional[str], service: str, level: str, message: str, timestamp: datetime):
        self.id = id
        self.service = service
        self.level = level
        self.message = message
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'service': self.service,
            'level': self.level,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }