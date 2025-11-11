from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LogCreateSchema(BaseModel):
    service: str
    level: str
    message: str

class LogResponseSchema(BaseModel):
    id: str
    service: str
    level: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True

class LogsQuerySchema(BaseModel):
    service: Optional[str] = None
    level: Optional[str] = None
    limit: int = 100