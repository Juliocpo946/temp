from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class TrainingSample:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        intervention_id: Optional[uuid.UUID],
        external_activity_id: int,
        window_data: Dict[str, Any],
        context_data: Dict[str, Any],
        label: str,  # CAMBIADO a str para soportar "no_intervention"
        source: str,
        created_at: Optional[datetime] = None,
        used_in_training: bool = False
    ):
        self.id = id or uuid.uuid4()
        self.intervention_id = intervention_id
        self.external_activity_id = external_activity_id
        self.window_data = window_data
        self.context_data = context_data
        self.label = label
        self.source = source
        self.created_at = created_at or datetime.utcnow()
        self.used_in_training = used_in_training

    def mark_as_used(self) -> None:
        self.used_in_training = True