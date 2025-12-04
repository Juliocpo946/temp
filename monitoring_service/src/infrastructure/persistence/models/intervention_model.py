from sqlalchemy import Column, String, Float, DateTime, Integer, JSON
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class InterventionModel(Base):
    __tablename__ = "interventions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    detection_decision_id = Column(CHAR(36), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(CHAR(36), nullable=False, index=True)
    activity_uuid = Column(CHAR(36), nullable=False, index=True)
    external_activity_id = Column(Integer, nullable=False, index=True)
    intervention_type = Column(String(20), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    pre_state_snapshot = Column(JSON, nullable=False)
    post_state_snapshot = Column(JSON, nullable=True)
    effectiveness_score = Column(Float, nullable=True)
    evaluated_at = Column(DateTime, nullable=True)
    evaluation_method = Column(String(50), nullable=True)