from pydantic import BaseModel
from typing import Optional

class ActivityStartSchema(BaseModel):
    external_activity_id: int
    title: str
    subtitle: Optional[str] = None
    content: Optional[str] = None
    activity_type: str

class ActivityCompleteSchema(BaseModel):
    external_activity_id: int
    feedback: dict

class ActivityAbandonSchema(BaseModel):
    external_activity_id: int
