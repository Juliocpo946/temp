from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TokenGenerateSchema(BaseModel):
    company_id: int

class TokenRevokeSchema(BaseModel):
    token: str

class TokenResponseSchema(BaseModel):
    token: str

class TokenValidationResponseSchema(BaseModel):
    valid: bool
    company_id: Optional[int] = None

    class Config:
        from_attributes = True
