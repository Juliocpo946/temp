from datetime import datetime
from typing import Optional
import uuid

class StateTransition:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        session_id: uuid.UUID,
        external_activity_id: int,
        from_state: str,
        to_state: str,
        transitioned_at: datetime,
        trigger_reason: str
    ):
        self.id = id or uuid.uuid4()
        self.session_id = session_id
        self.external_activity_id = external_activity_id
        self.from_state = from_state
        self.to_state = to_state
        self.transitioned_at = transitioned_at
        self.trigger_reason = trigger_reason