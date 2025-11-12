from datetime import datetime
from typing import Optional
import uuid

class Session:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        user_id: int,
        company_id: uuid.UUID,
        disability_type: str,
        cognitive_analysis_enabled: bool,
        status: str,
        current_activity: Optional[dict],
        created_at: datetime,
        last_heartbeat_at: datetime,
        ended_at: Optional[datetime]
    ):
        self.id = id or uuid.uuid4()
        self.user_id = user_id
        self.company_id = company_id
        self.disability_type = disability_type
        self.cognitive_analysis_enabled = cognitive_analysis_enabled
        self.status = status
        self.current_activity = current_activity
        self.created_at = created_at
        self.last_heartbeat_at = last_heartbeat_at
        self.ended_at = ended_at

    def update_heartbeat(self) -> None:
        self.last_heartbeat_at = datetime.utcnow()

    def pause(self) -> None:
        self.status = "pausada"

    def resume(self) -> None:
        self.status = "activa"

    def mark_paused_automatically(self) -> None:
        self.status = "pausada_automaticamente"

    def mark_expired(self) -> None:
        self.status = "expirada"

    def finalize(self) -> None:
        self.status = "finalizada"
        self.ended_at = datetime.utcnow()