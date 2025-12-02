from sqlalchemy import Column, String, Float, DateTime, Uuid
from datetime import datetime
import uuid
from src.infrastructure.persistence.database import Base

class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(Uuid, nullable=False, index=True)
    application_id = Column(Uuid, nullable=False, unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    external_id = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)