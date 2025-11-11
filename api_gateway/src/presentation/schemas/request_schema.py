from pydantic import BaseModel

class RequestSchema(BaseModel):
    token: str

class ProxyRequestSchema(BaseModel):
    path: str
    method: str