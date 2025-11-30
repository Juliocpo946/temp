from typing import Optional, List
from datetime import datetime

class SessionDTO:
    def __init__(
        self,
        id: str,
        user_id: int,
        company_id: str,
        disability_type: str,
        cognitive_analysis_enabled: bool,
        created_at: datetime,
        ended_at: Optional[datetime],
        activities: Optional[List[dict]] = None
    ):
        self.id = id
        self.user_id = user_id
        self.company_id = company_id
        self.disability_type = disability_type
        self.cognitive_analysis_enabled = cognitive_analysis_enabled
        self.created_at = created_at
        self.ended_at = ended_at
        self.activities = activities or []

    def to_dict(self) -> dict:
        return {
            'session_id': self.id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'disability_type': self.disability_type,
            'cognitive_analysis_enabled': self.cognitive_analysis_enabled,
            'created_at': self.created_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'is_active': self.ended_at is None,
            'activities': self.activities
        }