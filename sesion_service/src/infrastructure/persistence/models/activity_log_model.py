from sqlalchemy import Column, String, DateTime, Uuid, Integer, JSON, ForeignKey
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class ActivityLogModel(Base):
    __tablename__ = "activity_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    activity_uuid = Column(Uuid, unique=True, nullable=False, index=True)
    session_id = Column(Uuid, ForeignKey("sessions.id"), nullable=False)
    external_activity_id = Column(Integer, ForeignKey("external_activities.external_activity_id"), nullable=False)
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    paused_at = Column(DateTime, nullable=True)
    resumed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    feedback_data = Column(JSON, nullable=True)