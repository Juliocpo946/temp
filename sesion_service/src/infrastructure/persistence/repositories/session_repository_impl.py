from typing import Optional, List
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timedelta
import uuid
from src.domain.entities.session import Session
from src.domain.repositories.session_repository import SessionRepository
from src.infrastructure.persistence.models.session_model import SessionModel

class SessionRepositoryImpl(SessionRepository):
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, session: Session) -> Session:
        db_session = SessionModel(
            user_id=session.user_id,
            company_id=session.company_id,
            disability_type=session.disability_type,
            cognitive_analysis_enabled=session.cognitive_analysis_enabled
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return self._to_domain(db_session)

    def get_by_id(self, session_id: str) -> Optional[Session]:
        db_session = self.db.query(SessionModel).filter(
            SessionModel.id == uuid.UUID(session_id)
        ).first()
        return self._to_domain(db_session) if db_session else None

    def update(self, session: Session) -> Session:
        db_session = self.db.query(SessionModel).filter(
            SessionModel.id == session.id
        ).first()
        if db_session:
            db_session.ended_at = session.ended_at
            self.db.commit()
            self.db.refresh(db_session)
            return self._to_domain(db_session)
        return session

    def get_by_user_id(self, user_id: int) -> List[Session]:
        db_sessions = self.db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.ended_at.is_(None)
        ).all()
        return [self._to_domain(s) for s in db_sessions]

    def delete_old_sessions(self, hours: int) -> int:
        threshold = datetime.utcnow() - timedelta(hours=hours)
        result = self.db.query(SessionModel).filter(
            SessionModel.created_at < threshold,
            SessionModel.ended_at.is_(None)
        ).delete()
        self.db.commit()
        return result

    @staticmethod
    def _to_domain(db_session: SessionModel) -> Session:
        return Session(
            id=db_session.id,
            user_id=db_session.user_id,
            company_id=db_session.company_id,
            disability_type=db_session.disability_type,
            cognitive_analysis_enabled=db_session.cognitive_analysis_enabled,
            created_at=db_session.created_at,
            ended_at=db_session.ended_at
        )