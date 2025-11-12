from typing import Optional, List
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_
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
            cognitive_analysis_enabled=session.cognitive_analysis_enabled,
            status=session.status,
            current_activity=session.current_activity
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
            db_session.status = session.status
            db_session.current_activity = session.current_activity
            db_session.last_heartbeat_at = session.last_heartbeat_at
            db_session.ended_at = session.ended_at
            self.db.commit()
            self.db.refresh(db_session)
            return self._to_domain(db_session)
        return session

    def get_sessions_without_heartbeat(self, seconds: int) -> List[Session]:
        threshold = datetime.utcnow() - timedelta(seconds=seconds)
        db_sessions = self.db.query(SessionModel).filter(
            and_(
                SessionModel.status == "activa",
                SessionModel.last_heartbeat_at < threshold
            )
        ).all()
        return [self._to_domain(s) for s in db_sessions]

    def get_inactive_sessions(self, hours: int) -> List[Session]:
        threshold = datetime.utcnow() - timedelta(hours=hours)
        db_sessions = self.db.query(SessionModel).filter(
            and_(
                SessionModel.status.in_(["pausada", "pausada_automaticamente"]),
                SessionModel.last_heartbeat_at < threshold
            )
        ).all()
        return [self._to_domain(s) for s in db_sessions]

    @staticmethod
    def _to_domain(db_session: SessionModel) -> Session:
        return Session(
            id=db_session.id,
            user_id=db_session.user_id,
            company_id=db_session.company_id,
            disability_type=db_session.disability_type,
            cognitive_analysis_enabled=db_session.cognitive_analysis_enabled,
            status=db_session.status,
            current_activity=db_session.current_activity,
            created_at=db_session.created_at,
            last_heartbeat_at=db_session.last_heartbeat_at,
            ended_at=db_session.ended_at
        )