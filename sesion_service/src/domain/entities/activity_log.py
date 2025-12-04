from datetime import datetime
from typing import Optional
import uuid

class ActivityLog:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        activity_uuid: uuid.UUID,
        session_id: uuid.UUID,
        external_activity_id: int,
        status: str,
        started_at: datetime,
        paused_at: Optional[datetime],
        resumed_at: Optional[datetime],
        completed_at: Optional[datetime],
        feedback_data: Optional[dict],
        pause_count: int = 0  # NUEVO
    ):
        self.id = id or uuid.uuid4()
        self.activity_uuid = activity_uuid
        self.session_id = session_id
        self.external_activity_id = external_activity_id
        self.status = status
        self.started_at = started_at
        self.paused_at = paused_at
        self.resumed_at = resumed_at
        self.completed_at = completed_at
        self.feedback_data = feedback_data
        self.pause_count = pause_count  # NUEVO

    def pause(self) -> None:
        self.status = "pausada"
        self.paused_at = datetime.utcnow()
        self.pause_count += 1  # INCREMENTAR

    def resume(self) -> None:
        self.status = "en_progreso"
        self.resumed_at = datetime.utcnow()

    def complete(self, feedback_data: dict) -> None:
        self.status = "completada"
        self.completed_at = datetime.utcnow()
        self.feedback_data = feedback_data

    def abandon(self) -> None:
        self.status = "abandonada"
        self.completed_at = datetime.utcnow()

    def is_in_progress(self) -> bool:
        return self.status == "en_progreso"

    def is_paused(self) -> bool:
        return self.status == "pausada"