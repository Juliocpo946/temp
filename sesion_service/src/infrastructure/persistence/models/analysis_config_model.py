from sqlalchemy import Column, Boolean, Uuid, ForeignKey
import uuid
from src.infrastructure.persistence.database import Base

class AnalysisConfigModel(Base):
    __tablename__ = "analysis_configs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(Uuid, ForeignKey("sessions.id"), nullable=False, unique=True)
    cognitive_analysis_enabled = Column(Boolean, default=True)
    text_notifications = Column(Boolean, default=True)
    video_suggestions = Column(Boolean, default=True)
    vibration_alerts = Column(Boolean, default=True)
    pause_suggestions = Column(Boolean, default=True)