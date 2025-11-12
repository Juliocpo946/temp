from pydantic import BaseModel
from typing import Optional

class SessionCreateSchema(BaseModel):
    user_id: int
    disability_type: str
    cognitive_analysis_enabled: bool

class SessionResponseSchema(BaseModel):
    session_id: str
    status: str
    created_at: str

class HeartbeatResponseSchema(BaseModel):
    status: str
    last_heartbeat_at: str

class StatusResponseSchema(BaseModel):
    status: str