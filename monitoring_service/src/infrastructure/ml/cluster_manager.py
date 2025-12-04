from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DBSession
from src.infrastructure.persistence.repositories.cluster_repository import ClusterRepository
from src.domain.value_objects.cognitive_state import CognitiveState

class ClusterManager:
    def __init__(self, db: DBSession):
        self.cluster_repo = ClusterRepository(db)
        self.cluster_labels = {
            0: CognitiveState.ENGAGED.to_string(),
            1: CognitiveState.LIGHT_DISTRACTION.to_string(),
            2: CognitiveState.HEAVY_DISTRACTION.to_string(),
            3: CognitiveState.CONFUSION.to_string(),
            4: CognitiveState.FRUSTRATION.to_string(),
            5: CognitiveState.COGNITIVE_OVERLOAD.to_string(),
            6: CognitiveState.FATIGUE.to_string()
        }

    def save_cluster_metadata(
        self,
        cluster_id: int,
        centroid: List[float],
        sample_count: int,
        characteristics: Optional[Dict] = None
    ) -> None:
        label = self.cluster_labels.get(cluster_id, "unknown")
        chars = characteristics or {}
        
        self.cluster_repo.upsert(
            cluster_id=cluster_id,
            label=label,
            characteristics=chars,
            sample_count=sample_count,
            centroid=centroid
        )

    def get_cluster_label(self, cluster_id: int) -> str:
        db_cluster = self.cluster_repo.get_by_cluster_id(cluster_id)
        if db_cluster and db_cluster.label:
            return db_cluster.label
        return self.cluster_labels.get(cluster_id, "unknown")

    def get_all_clusters(self) -> List:
        return self.cluster_repo.get_all()

    def cleanup_stale_clusters(self, days: int = 30) -> int:
        return self.cluster_repo.delete_stale_clusters(days)