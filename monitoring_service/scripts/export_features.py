import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.cognitive_state_repository import CognitiveStateRepository

def export_features(days: int = 7, output_file: str = "features_export.json"):
    db: Session = SessionLocal()
    repo = CognitiveStateRepository(db)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    states = db.query(CognitiveStateModel).filter(
        CognitiveStateModel.started_at >= cutoff_date
    ).all()
    
    export_data = []
    for state in states:
        export_data.append({
            "user_id": state.user_id,
            "state_type": state.state_type,
            "cluster_id": state.cluster_id,
            "confidence_score": state.confidence_score,
            "stability_score": state.stability_score,
            "started_at": state.started_at.isoformat(),
            "duration_seconds": state.duration_seconds,
            "features_snapshot": state.features_snapshot
        })
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    db.close()
    print(f"[EXPORT_FEATURES] [INFO] Exportados {len(export_data)} estados a {output_file}")

if __name__ == "__main__":
    export_features()