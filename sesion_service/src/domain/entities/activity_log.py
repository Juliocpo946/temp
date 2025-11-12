from datetime import datetime
from typing import Optional
import uuid

class ActivityLog:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        session_id: uuid.UUID,
        external_activity_id: int,
        title: str,
        subtitle: Optional[str],
        content: Optional[str],
        activity_type: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime],
        feedback_data: Optional[dict]
    ):
        self.id = id or uuid.uuid4()
        self.session_id = session_id
        self.external_activity_id = external_activity_id
        self.title = title
        self.subtitle = subtitle
        self.content = content
        self.activity_type = activity_type
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.feedback_data = feedback_data

    def complete(self, feedback_data: dict) -> None:
        self.status = "completada"
        self.completed_at = datetime.utcnow()
        self.feedback_data = feedback_data

    def abandon(self) -> None:
        self.status = "abandonada"
        self.completed_at = datetime.utcnow()