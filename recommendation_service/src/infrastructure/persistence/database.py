from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.infrastructure.config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from src.infrastructure.persistence.models.content_model import ContentModel
    Base.metadata.create_all(bind=engine)