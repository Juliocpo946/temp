from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class CompanyCreateSchema(BaseModel):
    name: str
    email: EmailStr

class CompanyUpdateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class CompanyResponseSchema(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
