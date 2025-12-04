from sqlalchemy import Column, Integer, Float, DateTime, JSON
from datetime import datetime
from src.infrastructure.persistence.database import Base

class UserProfileModel(Base):
    __tablename__ = "user_cognitive_profiles"

    user_id = Column(Integer, primary_key=True, index=True)
    total_sessions = Column(Integer, default=0, nullable=False)
    state_frequencies = Column(JSON, nullable=False)
    common_transitions = Column(JSON, nullable=False)
    intervention_effectiveness = Column(JSON, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)