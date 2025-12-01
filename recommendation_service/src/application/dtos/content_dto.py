from typing import Optional
from pydantic import BaseModel


class CreateContentDTO(BaseModel):
    company_id: str
    topic: str
    subtopic: Optional[str] = None
    activity_type: Optional[str] = None
    intervention_type: str
    content_url: str
    content_type: str = "video"
    active: bool = True


class CreateContentFromUploadDTO(BaseModel):
    company_id: str
    topic: str
    subtopic: Optional[str] = None
    activity_type: Optional[str] = None
    intervention_type: str
    active: bool = True


class UpdateContentDTO(BaseModel):
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    activity_type: Optional[str] = None
    intervention_type: Optional[str] = None
    content_url: Optional[str] = None
    content_type: Optional[str] = None
    active: Optional[bool] = None


class ContentFilterDTO(BaseModel):
    company_id: Optional[str] = None
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    activity_type: Optional[str] = None
    intervention_type: Optional[str] = None
    active: Optional[bool] = None