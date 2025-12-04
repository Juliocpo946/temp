from sqlalchemy import Column, String, Float, DateTime, Integer, JSON
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class CognitiveStateModel(Base):
    __tablename__ = "cognitive_states"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(CHAR(36), nullable=False, index=True)
    activity_uuid = Column(CHAR(36), nullable=False, index=True)
    state_type = Column(String(50), nullable=False, index=True)
    cluster_id = Column(Integer, nullable=False)
    confidence_score = Column(Float, nullable=False)
    stability_score = Column(Float, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    features_snapshot = Column(JSON, nullable=True)
    previous_state_id = Column(CHAR(36), nullable=True)