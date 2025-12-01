from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
import uuid
from src.domain.entities.training_sample import TrainingSample
from src.infrastructure.persistence.models.training_sample_model import TrainingSampleModel

class TrainingSampleRepository:
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, sample: TrainingSample) -> TrainingSample:
        db_sample = TrainingSampleModel(
            id=str(sample.id),
            intervention_id=str(sample.intervention_id) if sample.intervention_id else None,
            external_activity_id=str(sample.external_activity_id),
            window_data=sample.window_data,
            context_data=sample.context_data,
            label=sample.label,
            source=sample.source,
            created_at=sample.created_at,
            used_in_training=sample.used_in_training
        )
        self.db.add(db_sample)
        self.db.commit()
        self.db.refresh(db_sample)
        return self._to_domain(db_sample)

    def get_for_training(self, source: str, limit: int = 1000) -> List[TrainingSample]:
        db_samples = self.db.query(TrainingSampleModel).filter(
            TrainingSampleModel.source == source,
            TrainingSampleModel.used_in_training == False
        ).limit(limit).all()
        return [self._to_domain(s) for s in db_samples]

    def mark_as_used(self, sample_ids: List[str]) -> None:
        self.db.query(TrainingSampleModel).filter(
            TrainingSampleModel.id.in_(sample_ids)
        ).update({"used_in_training": True}, synchronize_session=False)
        self.db.commit()

    def get_by_intervention_id(self, intervention_id: str) -> Optional[TrainingSample]:
        db_sample = self.db.query(TrainingSampleModel).filter(
            TrainingSampleModel.intervention_id == intervention_id
        ).first()
        return self._to_domain(db_sample) if db_sample else None

    def update_label(self, sample_id: str, new_label: int) -> None:
        self.db.query(TrainingSampleModel).filter(
            TrainingSampleModel.id == sample_id
        ).update({"label": new_label}, synchronize_session=False)
        self.db.commit()

    @staticmethod
    def _to_domain(db_sample: TrainingSampleModel) -> TrainingSample:
        return TrainingSample(
            id=uuid.UUID(db_sample.id),
            intervention_id=uuid.UUID(db_sample.intervention_id) if db_sample.intervention_id else None,
            external_activity_id=int(db_sample.external_activity_id),
            window_data=db_sample.window_data,
            context_data=db_sample.context_data,
            label=db_sample.label,
            source=db_sample.source,
            created_at=db_sample.created_at,
            used_in_training=db_sample.used_in_training
        )