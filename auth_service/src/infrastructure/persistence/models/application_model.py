from sqlalchemy import Column, String, Boolean, DateTime, Uuid, ForeignKey, Enum
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base
import enum

class PlatformType(str, enum.Enum):
    MOBILE = "mobile"
    WEB = "web"

class EnvironmentType(str, enum.Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"

class ApplicationModel(Base):
    __tablename__ = "applications"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(Uuid, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    environment = Column(Enum(EnvironmentType), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)