from datetime import datetime
from typing import Optional
import uuid

class PauseLog:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        session_id: uuid.UUID,
        pause_type: str,
        started_at: datetime,
        ended_at: Optional[datetime]
    ):
        self.id = id or uuid.uuid4()
        self.session_id = session_id
        self.pause_type = pause_type
        self.started_at = started_at
        self.ended_at = ended_at

    def end(self) -> None:
        self.ended_at = datetime.utcnow()