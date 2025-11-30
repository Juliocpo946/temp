from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from src.infrastructure.persistence.database import Base


class ContentModel(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tema = Column(String(100), nullable=False, index=True)
    subtema = Column(String(100), nullable=True, index=True)
    tipo_actividad = Column(String(100), nullable=True, index=True)
    tipo_intervencion = Column(String(50), nullable=False, index=True)
    contenido = Column(Text, nullable=False)
    activo = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())