from typing import Optional
from datetime import datetime

class ActivityDTO:
    def __init__(
        self,
        id: str,
        session_id: str,
        external_activity_id: int,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime],
        feedback_data: Optional[dict]
    ):
        self.id = id
        self.session_id = session_id
        self.external_activity_id = external_activity_id
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.feedback_data = feedback_data

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'external_activity_id': self.external_activity_id,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'feedback_data': self.feedback_data
        }