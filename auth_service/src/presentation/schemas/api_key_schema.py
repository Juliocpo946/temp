from pydantic import BaseModel
from typing import Optional

class ApiKeyGenerateSchema(BaseModel):
    application_id: str

class ApiKeyRevokeSchema(BaseModel):
    key_value: str

class ApiKeyResponseSchema(BaseModel):
    api_key: str

class ApiKeyValidationRequestSchema(BaseModel):
    key_value: str

class ApiKeyValidationResponseSchema(BaseModel):
    valid: bool
    company_id: Optional[str] = None
    application_id: Optional[str] = None

    class Config:
        from_attributes = True