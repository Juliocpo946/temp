from pydantic import BaseModel, EmailStr

class RequestLoginSchema(BaseModel):
    email: EmailStr

class VerifyLoginSchema(BaseModel):
    email: EmailStr
    otp_code: str