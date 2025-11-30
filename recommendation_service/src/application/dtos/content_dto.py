from typing import Optional
from pydantic import BaseModel


class CreateContentDTO(BaseModel):
    topic: str
    subtopic: Optional[str] = None
    activity_type: Optional[str] = None
    intervention_type: str
    content: str
    active: bool = True


class UpdateContentDTO(BaseModel):
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    activity_type: Optional[str] = None
    intervention_type: Optional[str] = None
    content: Optional[str] = None
    active: Optional[bool] = None


class ContentFilterDTO(BaseModel):
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    activity_type: Optional[str] = None
    intervention_type: Optional[str] = None
    active: Optional[bool] = None