from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class CognitiveStateEntity:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        user_id: int,
        session_id: uuid.UUID,
        activity_uuid: uuid.UUID,
        state_type: str,
        cluster_id: int,
        confidence_score: float,
        stability_score: float,
        started_at: datetime,
        ended_at: Optional[datetime] = None,
        duration_seconds: Optional[int] = None,
        features_snapshot: Optional[Dict[str, Any]] = None,
        previous_state_id: Optional[uuid.UUID] = None
    ):
        self.id = id or uuid.uuid4()
        self.user_id = user_id
        self.session_id = session_id
        self.activity_uuid = activity_uuid
        self.state_type = state_type
        self.cluster_id = cluster_id
        self.confidence_score = confidence_score
        self.stability_score = stability_score
        self.started_at = started_at
        self.ended_at = ended_at
        self.duration_seconds = duration_seconds
        self.features_snapshot = features_snapshot or {}
        self.previous_state_id = previous_state_id

    def end_state(self) -> None:
        self.ended_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())