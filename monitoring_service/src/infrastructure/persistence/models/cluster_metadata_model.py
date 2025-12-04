from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from datetime import datetime
from src.infrastructure.persistence.database import Base

class ClusterMetadataModel(Base):
    __tablename__ = "cluster_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    cluster_identifier = Column(Integer, nullable=False, unique=True, index=True)
    label = Column(String(50), nullable=True)
    characteristics = Column(JSON, nullable=False)
    sample_count = Column(Integer, default=0, nullable=False)
    centroid_features = Column(JSON, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)