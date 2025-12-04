from typing import Optional, List
from sqlalchemy.orm import Session as DBSession
from datetime import datetime
import uuid
from src.domain.entities.cognitive_state_entity import CognitiveStateEntity
from src.infrastructure.persistence.models.cognitive_state_model import CognitiveStateModel

class CognitiveStateRepository:
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, state: CognitiveStateEntity) -> CognitiveStateEntity:
        db_state = CognitiveStateModel(
            id=str(state.id),
            user_id=state.user_id,
            session_id=str(state.session_id),
            activity_uuid=str(state.activity_uuid),
            state_type=state.state_type,
            cluster_id=state.cluster_id,
            confidence_score=state.confidence_score,
            stability_score=state.stability_score,
            started_at=state.started_at,
            ended_at=state.ended_at,
            duration_seconds=state.duration_seconds,
            features_snapshot=state.features_snapshot,
            previous_state_id=str(state.previous_state_id) if state.previous_state_id else None
        )
        self.db.add(db_state)
        self.db.commit()
        self.db.refresh(db_state)
        return self._to_domain(db_state)

    def update(self, state: CognitiveStateEntity) -> CognitiveStateEntity:
        db_state = self.db.query(CognitiveStateModel).filter(
            CognitiveStateModel.id == str(state.id)
        ).first()
        if db_state:
            db_state.ended_at = state.ended_at
            db_state.duration_seconds = state.duration_seconds
            self.db.commit()
            self.db.refresh(db_state)
            return self._to_domain(db_state)
        return state

    def get_by_id(self, state_id: str) -> Optional[CognitiveStateEntity]:
        db_state = self.db.query(CognitiveStateModel).filter(
            CognitiveStateModel.id == state_id
        ).first()
        return self._to_domain(db_state) if db_state else None

    def get_recent_by_session(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[CognitiveStateEntity]:
        db_states = self.db.query(CognitiveStateModel).filter(
            CognitiveStateModel.session_id == session_id
        ).order_by(CognitiveStateModel.started_at.desc()).limit(limit).all()
        return [self._to_domain(s) for s in db_states]

    def get_active_state(
        self,
        session_id: str,
        activity_uuid: str
    ) -> Optional[CognitiveStateEntity]:
        db_state = self.db.query(CognitiveStateModel).filter(
            CognitiveStateModel.session_id == session_id,
            CognitiveStateModel.activity_uuid == activity_uuid,
            CognitiveStateModel.ended_at.is_(None)
        ).first()
        return self._to_domain(db_state) if db_state else None

    @staticmethod
    def _to_domain(db_state: CognitiveStateModel) -> CognitiveStateEntity:
        return CognitiveStateEntity(
            id=uuid.UUID(db_state.id),
            user_id=db_state.user_id,
            session_id=uuid.UUID(db_state.session_id),
            activity_uuid=uuid.UUID(db_state.activity_uuid),
            state_type=db_state.state_type,
            cluster_id=db_state.cluster_id,
            confidence_score=db_state.confidence_score,
            stability_score=db_state.stability_score,
            started_at=db_state.started_at,
            ended_at=db_state.ended_at,
            duration_seconds=db_state.duration_seconds,
            features_snapshot=db_state.features_snapshot,
            previous_state_id=uuid.UUID(db_state.previous_state_id) if db_state.previous_state_id else None
        )