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
        created_at: datetime,
        ended_at: Optional[datetime]
    ):
        self.id = id or uuid.uuid4()
        self.user_id = user_id
        self.company_id = company_id
        self.disability_type = disability_type
        self.cognitive_analysis_enabled = cognitive_analysis_enabled
        self.created_at = created_at
        self.ended_at = ended_at

    def finalize(self) -> None:
        self.ended_at = datetime.utcnow()

    def is_active(self) -> bool:
        return self.ended_at is None