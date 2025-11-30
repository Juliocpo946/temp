from typing import List
from sqlalchemy.orm import Session as DBSession
import uuid
from src.domain.entities.state_transition import StateTransition
from src.infrastructure.persistence.models.state_transition_model import StateTransitionModel

class StateTransitionRepository:
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, transition: StateTransition) -> StateTransition:
        db_transition = StateTransitionModel(
            id=str(transition.id),
            session_id=str(transition.session_id),
            external_activity_id=str(transition.external_activity_id),
            from_state=transition.from_state,
            to_state=transition.to_state,
            transitioned_at=transition.transitioned_at,
            trigger_reason=transition.trigger_reason
        )
        self.db.add(db_transition)
        self.db.commit()
        self.db.refresh(db_transition)
        return self._to_domain(db_transition)

    def get_by_session(self, session_id: str) -> List[StateTransition]:
        db_transitions = self.db.query(StateTransitionModel).filter(
            StateTransitionModel.session_id == session_id
        ).order_by(StateTransitionModel.transitioned_at.desc()).all()
        return [self._to_domain(t) for t in db_transitions]

    @staticmethod
    def _to_domain(db_transition: StateTransitionModel) -> StateTransition:
        return StateTransition(
            id=uuid.UUID(db_transition.id),
            session_id=uuid.UUID(db_transition.session_id),
            external_activity_id=int(db_transition.external_activity_id),
            from_state=db_transition.from_state,
            to_state=db_transition.to_state,
            transitioned_at=db_transition.transitioned_at,
            trigger_reason=db_transition.trigger_reason
        )