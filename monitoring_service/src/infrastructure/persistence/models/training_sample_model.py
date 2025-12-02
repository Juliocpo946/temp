from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class TrainingSampleModel(Base):
    __tablename__ = "training_samples"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    intervention_id = Column(CHAR(36), ForeignKey("interventions.id"), nullable=True)
    external_activity_id = Column(String(50), nullable=False)
    window_data = Column(JSON, nullable=False)
    context_data = Column(JSON, nullable=False)
    label = Column(String(50), nullable=False)  # CAMBIADO de Integer a String
    source = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    used_in_training = Column(Boolean, default=False, nullable=False)