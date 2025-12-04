from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session as DBSession
from src.infrastructure.persistence.models.cluster_metadata_model import ClusterMetadataModel
from datetime import datetime

class ClusterRepository:
    def __init__(self, db: DBSession):
        self.db = db

    def upsert(
        self,
        cluster_id: int,
        label: Optional[str],
        characteristics: Dict[str, Any],
        sample_count: int,
        centroid: List[float]
    ) -> ClusterMetadataModel:
        db_cluster = self.db.query(ClusterMetadataModel).filter(
            ClusterMetadataModel.cluster_identifier == cluster_id
        ).first()

        if db_cluster:
            db_cluster.label = label
            db_cluster.characteristics = characteristics
            db_cluster.sample_count = sample_count
            db_cluster.centroid_features = centroid
            db_cluster.last_updated = datetime.utcnow()
        else:
            db_cluster = ClusterMetadataModel(
                cluster_identifier=cluster_id,
                label=label,
                characteristics=characteristics,
                sample_count=sample_count,
                centroid_features=centroid,
                last_updated=datetime.utcnow()
            )
            self.db.add(db_cluster)

        self.db.commit()
        self.db.refresh(db_cluster)
        return db_cluster

    def get_by_cluster_id(self, cluster_id: int) -> Optional[ClusterMetadataModel]:
        return self.db.query(ClusterMetadataModel).filter(
            ClusterMetadataModel.cluster_identifier == cluster_id
        ).first()

    def get_all(self) -> List[ClusterMetadataModel]:
        return self.db.query(ClusterMetadataModel).all()

    def delete_stale_clusters(self, days: int = 30) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = self.db.query(ClusterMetadataModel).filter(
            ClusterMetadataModel.last_updated < cutoff_date
        ).delete()
        self.db.commit()
        return deleted