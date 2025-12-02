from datetime import datetime
from typing import Optional
import uuid

class Intervention:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        session_id: uuid.UUID,
        activity_uuid: uuid.UUID,
        user_id: int,
        external_activity_id: int,
        intervention_type: str,
        cognitive_event: str,
        confidence: float,
        precision: float,
        triggered_at: datetime,  # RENOMBRADO de created_at
        result: Optional[str] = "pending",
        evaluated_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.session_id = session_id
        self.activity_uuid = activity_uuid
        self.user_id = user_id
        self.external_activity_id = external_activity_id
        self.intervention_type = intervention_type
        self.cognitive_event = cognitive_event
        self.confidence = confidence
        self.precision = precision
        self.triggered_at = triggered_at
        self.result = result
        self.evaluated_at = evaluated_at

    def evaluate_result(self, result: str) -> None:
        self.result = result
        self.evaluated_at = datetime.utcnow()