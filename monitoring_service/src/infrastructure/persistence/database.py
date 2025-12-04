from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.infrastructure.config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    import src.infrastructure.persistence.models.intervention_model
    import src.infrastructure.persistence.models.cognitive_state_model
    import src.infrastructure.persistence.models.detection_decision_model
    import src.infrastructure.persistence.models.cluster_metadata_model
    import src.infrastructure.persistence.models.user_profile_model
    
    Base.metadata.create_all(bind=engine)
    print(f"[DATABASE] [INFO] Tablas creadas exitosamente")