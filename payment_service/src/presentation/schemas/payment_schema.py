from pydantic import BaseModel, HttpUrl

class CreatePaymentLinkSchema(BaseModel):
    application_id: str
    success_url: HttpUrl
    cancel_url: HttpUrl