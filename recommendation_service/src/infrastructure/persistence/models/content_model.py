from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Uuid
from sqlalchemy.sql import func
import uuid
from src.infrastructure.persistence.database import Base


class ContentModel(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Uuid, nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    subtopic = Column(String(100), nullable=True, index=True)
    activity_type = Column(String(100), nullable=True, index=True)
    intervention_type = Column(String(50), nullable=False, index=True)
    content_url = Column(Text, nullable=False)
    content_type = Column(String(20), nullable=False, default="video")
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())