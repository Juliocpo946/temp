from typing import Optional, List
from datetime import datetime
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
            session_id=str(intervention.session_id),
            activity_uuid=str(intervention.activity_uuid),
            external_activity_id=str(intervention.external_activity_id),
            intervention_type=intervention.intervention_type,
            confidence=intervention.confidence,
            triggered_at=intervention.triggered_at,
            window_snapshot=intervention.window_snapshot,
            context_snapshot=intervention.context_snapshot,
            result=intervention.result,
            result_evaluated_at=intervention.result_evaluated_at
        )
        self.db.add(db_intervention)
        self.db.commit()
        self.db.refresh(db_intervention)
        return self._to_domain(db_intervention)

    def get_by_id(self, intervention_id: str) -> Optional[Intervention]:
        db_intervention = self.db.query(InterventionModel).filter(
            InterventionModel.id == intervention_id
        ).first()
        return self._to_domain(db_intervention) if db_intervention else None

    def get_by_activity_uuid(self, activity_uuid: str) -> List[Intervention]:
        db_interventions = self.db.query(InterventionModel).filter(
            InterventionModel.activity_uuid == activity_uuid
        ).order_by(InterventionModel.triggered_at.desc()).all()
        return [self._to_domain(i) for i in db_interventions]

    def get_pending_evaluations(self, before: datetime) -> List[Intervention]:
        db_interventions = self.db.query(InterventionModel).filter(
            InterventionModel.result == "pending",
            InterventionModel.triggered_at < before
        ).all()
        return [self._to_domain(i) for i in db_interventions]

    def update(self, intervention: Intervention) -> Intervention:
        db_intervention = self.db.query(InterventionModel).filter(
            InterventionModel.id == str(intervention.id)
        ).first()
        if db_intervention:
            db_intervention.result = intervention.result
            db_intervention.result_evaluated_at = intervention.result_evaluated_at
            self.db.commit()
            self.db.refresh(db_intervention)
            return self._to_domain(db_intervention)
        return intervention

    @staticmethod
    def _to_domain(db_intervention: InterventionModel) -> Intervention:
        return Intervention(
            id=uuid.UUID(db_intervention.id),
            session_id=uuid.UUID(db_intervention.session_id),
            activity_uuid=uuid.UUID(db_intervention.activity_uuid),
            external_activity_id=int(db_intervention.external_activity_id),
            intervention_type=db_intervention.intervention_type,
            confidence=db_intervention.confidence,
            triggered_at=db_intervention.triggered_at,
            window_snapshot=db_intervention.window_snapshot,
            context_snapshot=db_intervention.context_snapshot,
            result=db_intervention.result,
            result_evaluated_at=db_intervention.result_evaluated_at
        )