from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session as DBSession
import uuid
from src.domain.entities.intervention import Intervention
from src.infrastructure.persistence.models.intervention_model import InterventionModel

class InterventionRepository:
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, intervention: Intervention) -> Intervention:
        db_intervention = InterventionModel(
            id=str(intervention.id),
            detection_decision_id=str(intervention.detection_decision_id),
            user_id=intervention.user_id,
            session_id=str(intervention.session_id),
            activity_uuid=str(intervention.activity_uuid),
            external_activity_id=intervention.external_activity_id,
            intervention_type=intervention.intervention_type,
            triggered_at=intervention.triggered_at,
            pre_state_snapshot=intervention.pre_state_snapshot,
            post_state_snapshot=intervention.post_state_snapshot,
            effectiveness_score=intervention.effectiveness_score,
            evaluated_at=intervention.evaluated_at,
            evaluation_method=intervention.evaluation_method
        )
        self.db.add(db_intervention)
        self.db.commit()
        self.db.refresh(db_intervention)
        return self._to_domain(db_intervention)

    def update(self, intervention: Intervention) -> Intervention:
        db_intervention = self.db.query(InterventionModel).filter(
            InterventionModel.id == str(intervention.id)
        ).first()
        if db_intervention:
            db_intervention.post_state_snapshot = intervention.post_state_snapshot
            db_intervention.effectiveness_score = intervention.effectiveness_score
            db_intervention.evaluated_at = intervention.evaluated_at
            db_intervention.evaluation_method = intervention.evaluation_method
            self.db.commit()
            self.db.refresh(db_intervention)
            return self._to_domain(db_intervention)
        return intervention

    def get_by_id(self, intervention_id: str) -> Optional[Intervention]:
        db_intervention = self.db.query(InterventionModel).filter(
            InterventionModel.id == intervention_id
        ).first()
        return self._to_domain(db_intervention) if db_intervention else None

    def get_pending_evaluations(self, before: datetime) -> List[Intervention]:
        db_interventions = self.db.query(InterventionModel).filter(
            InterventionModel.effectiveness_score.is_(None),
            InterventionModel.triggered_at < before
        ).all()
        return [self._to_domain(i) for i in db_interventions]

    def get_recent_by_user(
        self,
        user_id: int,
        intervention_type: Optional[str] = None,
        hours: int = 24
    ) -> List[Intervention]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = self.db.query(InterventionModel).filter(
            InterventionModel.user_id == user_id,
            InterventionModel.triggered_at >= cutoff_time
        )
        if intervention_type:
            query = query.filter(InterventionModel.intervention_type == intervention_type)
        
        db_interventions = query.order_by(InterventionModel.triggered_at.desc()).all()
        return [self._to_domain(i) for i in db_interventions]

    @staticmethod
    def _to_domain(db_intervention: InterventionModel) -> Intervention:
        return Intervention(
            id=uuid.UUID(db_intervention.id),
            detection_decision_id=uuid.UUID(db_intervention.detection_decision_id),
            user_id=db_intervention.user_id,
            session_id=uuid.UUID(db_intervention.session_id),
            activity_uuid=uuid.UUID(db_intervention.activity_uuid),
            external_activity_id=db_intervention.external_activity_id,
            intervention_type=db_intervention.intervention_type,
            triggered_at=db_intervention.triggered_at,
            pre_state_snapshot=db_intervention.pre_state_snapshot,
            post_state_snapshot=db_intervention.post_state_snapshot,
            effectiveness_score=db_intervention.effectiveness_score,
            evaluated_at=db_intervention.evaluated_at,
            evaluation_method=db_intervention.evaluation_method
        )