from typing import Optional
from datetime import datetime

class SessionDTO:
    def __init__(
        self,
        id: str,
        user_id: int,
        company_id: str,
        disability_type: str,
        cognitive_analysis_enabled: bool,
        status: str,
        current_activity: Optional[dict],
        created_at: datetime,
        last_heartbeat_at: datetime,
        ended_at: Optional[datetime]
    ):
        self.id = id
        self.user_id = user_id
        self.company_id = company_id
        self.disability_type = disability_type
        self.cognitive_analysis_enabled = cognitive_analysis_enabled
        self.status = status
        self.current_activity = current_activity
        self.created_at = created_at
        self.last_heartbeat_at = last_heartbeat_at
        self.ended_at = ended_at

    def to_dict(self) -> dict:
        return {
            'session_id': str(self.id),
            'user_id': self.user_id,
            'company_id': str(self.company_id),
            'disability_type': self.disability_type,
            'cognitive_analysis_enabled': self.cognitive_analysis_enabled,
            'status': self.status,
            'current_activity': self.current_activity,
            'created_at': self.created_at.isoformat(),
            'last_heartbeat_at': self.last_heartbeat_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }