from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class Intervention:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        detection_decision_id: uuid.UUID,
        user_id: int,
        session_id: uuid.UUID,
        activity_uuid: uuid.UUID,
        external_activity_id: int,
        intervention_type: str,
        triggered_at: datetime,
        pre_state_snapshot: Dict[str, Any],
        post_state_snapshot: Optional[Dict[str, Any]] = None,
        effectiveness_score: Optional[float] = None,
        evaluated_at: Optional[datetime] = None,
        evaluation_method: Optional[str] = None
    ):
        self.id = id or uuid.uuid4()
        self.detection_decision_id = detection_decision_id
        self.user_id = user_id
        self.session_id = session_id
        self.activity_uuid = activity_uuid
        self.external_activity_id = external_activity_id
        self.intervention_type = intervention_type
        self.triggered_at = triggered_at
        self.pre_state_snapshot = pre_state_snapshot
        self.post_state_snapshot = post_state_snapshot
        self.effectiveness_score = effectiveness_score
        self.evaluated_at = evaluated_at
        self.evaluation_method = evaluation_method

    def evaluate(
        self,
        effectiveness_score: float,
        post_state_snapshot: Dict[str, Any],
        evaluation_method: str
    ) -> None:
        self.effectiveness_score = effectiveness_score
        self.post_state_snapshot = post_state_snapshot
        self.evaluated_at = datetime.utcnow()
        self.evaluation_method = evaluation_method