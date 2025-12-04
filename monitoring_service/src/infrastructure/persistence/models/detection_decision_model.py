from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class DetectionDecisionModel(Base):
    __tablename__ = "detection_decisions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    cognitive_state_id = Column(CHAR(36), nullable=False, index=True)
    should_intervene = Column(Boolean, nullable=False)
    intervention_type = Column(String(20), nullable=True)
    decision_score = Column(Float, nullable=False)
    reason_code = Column(String(50), nullable=False)
    cooldown_active = Column(Boolean, nullable=False)
    cooldown_until = Column(DateTime, nullable=True)
    context_data = Column(JSON, nullable=False)
    decided_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)