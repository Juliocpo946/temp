from sqlalchemy import create_engine, text
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
    # IMPORTANTE: Importar los modelos aquí para que se registren en Base.metadata
    # antes de llamar a create_all
    import src.infrastructure.persistence.models.intervention_model
    import src.infrastructure.persistence.models.training_sample_model
    import src.infrastructure.persistence.models.state_transition_model
    
    Base.metadata.create_all(bind=engine)
    print(f"[DATABASE] [INFO] Tablas creadas exitosamente")