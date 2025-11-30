from sqlalchemy import Column, String, Float, DateTime, JSON, Enum
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class InterventionModel(Base):
    __tablename__ = "interventions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(CHAR(36), nullable=False, index=True)
    external_activity_id = Column(String(50), nullable=False, index=True)
    intervention_type = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    window_snapshot = Column(JSON, nullable=False)
    context_snapshot = Column(JSON, nullable=False)
    result = Column(String(20), default="pending", nullable=False)
    result_evaluated_at = Column(DateTime, nullable=True)