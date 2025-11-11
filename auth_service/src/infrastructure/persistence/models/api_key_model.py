from sqlalchemy import Column, String, Boolean, DateTime, Uuid, ForeignKey
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class ApiKeyModel(Base):
    __tablename__ = "api_keys"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    key_value = Column(String(500), unique=True, nullable=False, index=True)
    company_id = Column(Uuid, ForeignKey("companies.id"), nullable=False)
    application_id = Column(Uuid, ForeignKey("applications.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)