from sqlalchemy import Column, String, DateTime, Uuid, Integer
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class ExternalActivityModel(Base):
    __tablename__ = "external_activities"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    external_activity_id = Column(Integer, nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    subtitle = Column(String(500), nullable=True)
    content = Column(String(2000), nullable=True)
    activity_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)