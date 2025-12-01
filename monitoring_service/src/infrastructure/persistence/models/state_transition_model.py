from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class StateTransitionModel(Base):
    __tablename__ = "state_transitions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(CHAR(36), nullable=False, index=True)
    external_activity_id = Column(String(50), nullable=False, index=True)
    from_state = Column(String(50), nullable=False)
    to_state = Column(String(50), nullable=False)
    transitioned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    trigger_reason = Column(String(100), nullable=False)