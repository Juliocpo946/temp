from typing import Optional
from datetime import datetime

class ActivityDTO:
    def __init__(
        self,
        activity_uuid: str,
        session_id: str,
        external_activity_id: int,
        status: str,
        started_at: datetime,
        paused_at: Optional[datetime],
        resumed_at: Optional[datetime],
        completed_at: Optional[datetime]
    ):
        self.activity_uuid = activity_uuid
        self.session_id = session_id
        self.external_activity_id = external_activity_id
        self.status = status
        self.started_at = started_at
        self.paused_at = paused_at
        self.resumed_at = resumed_at
        self.completed_at = completed_at

    def to_dict(self) -> dict:
        return {
            'activity_uuid': self.activity_uuid,
            'session_id': self.session_id,
            'external_activity_id': self.external_activity_id,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'paused_at': self.paused_at.isoformat() if self.paused_at else None,
            'resumed_at': self.resumed_at.isoformat() if self.resumed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }