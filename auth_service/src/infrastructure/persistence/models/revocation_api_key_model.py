from sqlalchemy import Column, String, Boolean, DateTime, Uuid, ForeignKey
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class RevocationApiKeyModel(Base):
    __tablename__ = "revocation_api_keys"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    api_key_id = Column(Uuid, ForeignKey("api_keys.id"), nullable=False)
    confirmation_code = Column(String(6), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)