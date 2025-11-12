from sqlalchemy import Column, String, DateTime, Uuid, ForeignKey
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class PauseLogModel(Base):
    __tablename__ = "pause_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(Uuid, ForeignKey("sessions.id"), nullable=False)
    pause_type = Column(String(50), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)