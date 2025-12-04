from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.cluster_repository import ClusterRepository
from src.domain.value_objects.cognitive_state import CognitiveState

def seed_clusters():
    db: Session = SessionLocal()
    repo = ClusterRepository(db)
    
    clusters = [
        {
            "cluster_id": 0,
            "label": CognitiveState.ENGAGED.to_string(),
            "characteristics": {"description": "Usuario completamente enfocado y productivo"},
            "sample_count": 0,
            "centroid": [0.8, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.3]
        },
        {
            "cluster_id": 1,
            "label": CognitiveState.LIGHT_DISTRACTION.to_string(),
            "characteristics": {"description": "Usuario temporalmente distraido"},
            "sample_count": 0,
            "centroid": [0.5, 0.3, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 0.2, 0.2, 0.0, 0.3]
        },
        {
            "cluster_id": 2,
            "label": CognitiveState.HEAVY_DISTRACTION.to_string(),
            "characteristics": {"description": "Usuario consistentemente distraido"},
            "sample_count": 0,
            "centroid": [0.3, 0.4, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.4, 0.4, 0.2, 0.25]
        },
        {
            "cluster_id": 3,
            "label": CognitiveState.CONFUSION.to_string(),
            "characteristics": {"description": "Usuario confundido con el contenido"},
            "sample_count": 0,
            "centroid": [0.2, 0.3, 0.2, 0.1, 0.1, 0.0, 0.1, 0.0, 0.7, 0.1, 0.1, 0.0, 0.3]
        },
        {
            "cluster_id": 4,
            "label": CognitiveState.FRUSTRATION.to_string(),
            "characteristics": {"description": "Usuario frustrado"},
            "sample_count": 0,
            "centroid": [0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.0, 0.0, 0.7, 0.0, 0.0, 0.0, 0.3]
        },
        {
            "cluster_id": 5,
            "label": CognitiveState.COGNITIVE_OVERLOAD.to_string(),
            "characteristics": {"description": "Usuario sobrecargado cognitivamente"},
            "sample_count": 0,
            "centroid": [0.1, 0.1, 0.1, 0.3, 0.2, 0.1, 0.1, 0.0, 0.5, 0.2, 0.2, 0.0, 0.28]
        },
        {
            "cluster_id": 6,
            "label": CognitiveState.FATIGUE.to_string(),
            "characteristics": {"description": "Usuario fatigado"},
            "sample_count": 0,
            "centroid": [0.2, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.4, 0.1, 0.1, 0.5, 0.2]
        }
    ]
    
    for cluster_data in clusters:
        repo.upsert(
            cluster_id=cluster_data["cluster_id"],
            label=cluster_data["label"],
            characteristics=cluster_data["characteristics"],
            sample_count=cluster_data["sample_count"],
            centroid=cluster_data["centroid"]
        )
    
    db.close()
    print("[SEED_CLUSTERS] [INFO] Clusters inicializados correctamente")

if __name__ == "__main__":
    seed_clusters()