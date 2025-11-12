from sqlalchemy import Column, String, Boolean, DateTime, Uuid, Integer, JSON
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, nullable=False)
    company_id = Column(Uuid, nullable=False)
    disability_type = Column(String(100), nullable=False)
    cognitive_analysis_enabled = Column(Boolean, default=True)
    status = Column(String(50), nullable=False)
    current_activity = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)