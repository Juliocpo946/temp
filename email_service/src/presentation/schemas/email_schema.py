from pydantic import BaseModel, EmailStr

class SendEmailSchema(BaseModel):
    to_email: EmailStr
    subject: str
    html_body: str