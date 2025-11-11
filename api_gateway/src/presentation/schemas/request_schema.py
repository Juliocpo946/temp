from pydantic import BaseModel

class RequestSchema(BaseModel):
    api_key: str

class ProxyRequestSchema(BaseModel):
    path: str
    method: str