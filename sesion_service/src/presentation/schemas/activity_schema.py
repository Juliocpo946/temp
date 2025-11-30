from pydantic import BaseModel
from typing import Optional

class ActivityStartSchema(BaseModel):
    external_activity_id: int
    title: str
    subtitle: Optional[str] = None
    content: Optional[str] = None
    activity_type: str

class ActivityCompleteSchema(BaseModel):
    feedback: dict

class ActivityResponseSchema(BaseModel):
    status: str
    activity_uuid: str