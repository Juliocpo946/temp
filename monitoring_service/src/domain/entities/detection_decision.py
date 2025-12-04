from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class DetectionDecision:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        cognitive_state_id: uuid.UUID,
        should_intervene: bool,
        intervention_type: Optional[str],
        decision_score: float,
        reason_code: str,
        cooldown_active: bool,
        cooldown_until: Optional[datetime],
        context_data: Dict[str, Any],
        decided_at: datetime
    ):
        self.id = id or uuid.uuid4()
        self.cognitive_state_id = cognitive_state_id
        self.should_intervene = should_intervene
        self.intervention_type = intervention_type
        self.decision_score = decision_score
        self.reason_code = reason_code
        self.cooldown_active = cooldown_active
        self.cooldown_until = cooldown_until
        self.context_data = context_data
        self.decided_at = decided_at