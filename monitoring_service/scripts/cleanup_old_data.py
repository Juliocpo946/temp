from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.models.cognitive_state_model import CognitiveStateModel
from src.infrastructure.persistence.models.intervention_model import InterventionModel

def cleanup_old_data(days: int = 90):
    db: Session = SessionLocal()
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    deleted_states = db.query(CognitiveStateModel).filter(
        CognitiveStateModel.started_at < cutoff_date
    ).delete()
    
    deleted_interventions = db.query(InterventionModel).filter(
        InterventionModel.triggered_at < cutoff_date
    ).delete()
    
    db.commit()
    db.close()
    
    print(f"[CLEANUP] [INFO] Eliminados {deleted_states} estados cognitivos")
    print(f"[CLEANUP] [INFO] Eliminadas {deleted_interventions} intervenciones")
    print(f"[CLEANUP] [INFO] Datos anteriores a {cutoff_date.date()} eliminados")

if __name__ == "__main__":
    cleanup_old_data()