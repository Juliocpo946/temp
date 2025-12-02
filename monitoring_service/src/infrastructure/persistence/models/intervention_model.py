from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class InterventionModel(Base):
    __tablename__ = "interventions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(CHAR(36), nullable=False, index=True)
    activity_uuid = Column(CHAR(36), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # NUEVO
    external_activity_id = Column(Integer, nullable=False, index=True)
    intervention_type = Column(String(20), nullable=False)
    cognitive_event = Column(String(50), nullable=False)   # NUEVO
    confidence = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)              # NUEVO
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    result = Column(String(20), default="pending", nullable=False)
    result_evaluated_at = Column(DateTime, nullable=True)