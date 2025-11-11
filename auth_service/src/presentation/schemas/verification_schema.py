from pydantic import BaseModel, EmailStr

class RequestVerificationSchema(BaseModel):
    name: str
    email: EmailStr

class ConfirmVerificationSchema(BaseModel):
    name: str
    email: EmailStr
    verification_code: str