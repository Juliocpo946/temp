from sqlalchemy import Column, String, Boolean, DateTime, Uuid
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class CompanyModel(Base):
    __tablename__ = "companies"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)