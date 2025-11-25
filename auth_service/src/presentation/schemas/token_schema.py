from pydantic import BaseModel
from typing import Optional

class ValidateTokenSchema(BaseModel):
    token: str

class TokenValidationResponseSchema(BaseModel):
    valid: bool
    company_id: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True