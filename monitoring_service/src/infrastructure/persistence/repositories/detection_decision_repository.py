from typing import Optional
from sqlalchemy.orm import Session as DBSession
import uuid
from src.domain.entities.detection_decision import DetectionDecision
from src.infrastructure.persistence.models.detection_decision_model import DetectionDecisionModel

class DetectionDecisionRepository:
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, decision: DetectionDecision) -> DetectionDecision:
        db_decision = DetectionDecisionModel(
            id=str(decision.id),
            cognitive_state_id=str(decision.cognitive_state_id),
            should_intervene=decision.should_intervene,
            intervention_type=decision.intervention_type,
            decision_score=decision.decision_score,
            reason_code=decision.reason_code,
            cooldown_active=decision.cooldown_active,
            cooldown_until=decision.cooldown_until,
            context_data=decision.context_data,
            decided_at=decision.decided_at
        )
        self.db.add(db_decision)
        self.db.commit()
        self.db.refresh(db_decision)
        return self._to_domain(db_decision)

    def get_by_id(self, decision_id: str) -> Optional[DetectionDecision]:
        db_decision = self.db.query(DetectionDecisionModel).filter(
            DetectionDecisionModel.id == decision_id
        ).first()
        return self._to_domain(db_decision) if db_decision else None

    @staticmethod
    def _to_domain(db_decision: DetectionDecisionModel) -> DetectionDecision:
        return DetectionDecision(
            id=uuid.UUID(db_decision.id),
            cognitive_state_id=uuid.UUID(db_decision.cognitive_state_id),
            should_intervene=db_decision.should_intervene,
            intervention_type=db_decision.intervention_type,
            decision_score=db_decision.decision_score,
            reason_code=db_decision.reason_code,
            cooldown_active=db_decision.cooldown_active,
            cooldown_until=db_decision.cooldown_until,
            context_data=db_decision.context_data,
            decided_at=db_decision.decided_at
        )