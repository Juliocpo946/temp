from datetime import datetime
from typing import Optional

class Log:
    def __init__(self, id: Optional[str], service: str, level: str, message: str, timestamp: datetime):
        self.id = id
        self.service = service
        self.level = level
        self.message = message
        self.timestamp = timestamp