from typing import Optional, Dict, Any
from sqlalchemy.orm import Session as DBSession
from src.infrastructure.persistence.models.user_profile_model import UserProfileModel
from datetime import datetime

class UserProfileRepository:
    def __init__(self, db: DBSession):
        self.db = db

    def upsert(
        self,
        user_id: int,
        total_sessions: int,
        state_frequencies: Dict[str, float],
        common_transitions: Dict[str, int],
        intervention_effectiveness: Dict[str, float]
    ) -> UserProfileModel:
        db_profile = self.db.query(UserProfileModel).filter(
            UserProfileModel.user_id == user_id
        ).first()

        if db_profile:
            db_profile.total_sessions = total_sessions
            db_profile.state_frequencies = state_frequencies
            db_profile.common_transitions = common_transitions
            db_profile.intervention_effectiveness = intervention_effectiveness
            db_profile.last_updated = datetime.utcnow()
        else:
            db_profile = UserProfileModel(
                user_id=user_id,
                total_sessions=total_sessions,
                state_frequencies=state_frequencies,
                common_transitions=common_transitions,
                intervention_effectiveness=intervention_effectiveness,
                last_updated=datetime.utcnow()
            )
            self.db.add(db_profile)

        self.db.commit()
        self.db.refresh(db_profile)
        return db_profile

    def get_by_user_id(self, user_id: int) -> Optional[UserProfileModel]:
        return self.db.query(UserProfileModel).filter(
            UserProfileModel.user_id == user_id
        ).first()

    def increment_sessions(self, user_id: int) -> None:
        db_profile = self.get_by_user_id(user_id)
        if db_profile:
            db_profile.total_sessions += 1
            db_profile.last_updated = datetime.utcnow()
            self.db.commit()