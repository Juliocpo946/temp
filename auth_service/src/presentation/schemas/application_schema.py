from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ApplicationCreateSchema(BaseModel):
    name: str
    platform: str
    environment: str

class ApplicationResponseSchema(BaseModel):
    id: str
    company_id: str
    name: str
    platform: str
    environment: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ApiKeyResponseSchema(BaseModel):
    api_key: str

class ConfirmRevokeSchema(BaseModel):
    confirmation_code: str