from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class Intervention:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        session_id: uuid.UUID,
        external_activity_id: int,
        intervention_type: str,
        confidence: float,
        triggered_at: datetime,
        window_snapshot: Dict[str, Any],
        context_snapshot: Dict[str, Any],
        result: str = "pending",
        result_evaluated_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.session_id = session_id
        self.external_activity_id = external_activity_id
        self.intervention_type = intervention_type
        self.confidence = confidence
        self.triggered_at = triggered_at
        self.window_snapshot = window_snapshot
        self.context_snapshot = context_snapshot
        self.result = result
        self.result_evaluated_at = result_evaluated_at

    def evaluate_result(self, result: str) -> None:
        self.result = result
        self.result_evaluated_at = datetime.utcnow()