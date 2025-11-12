from sqlalchemy import Column, String, DateTime, Uuid, Integer, JSON, ForeignKey
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class ActivityLogModel(Base):
    __tablename__ = "activity_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(Uuid, ForeignKey("sessions.id"), nullable=False)
    external_activity_id = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    subtitle = Column(String(500), nullable=True)
    content = Column(String, nullable=True)
    activity_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    feedback_data = Column(JSON, nullable=True)