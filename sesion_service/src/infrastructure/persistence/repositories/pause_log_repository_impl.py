from typing import Optional
from sqlalchemy.orm import Session as DBSession
import uuid
from src.domain.entities.pause_log import PauseLog
from src.domain.repositories.pause_log_repository import PauseLogRepository
from src.infrastructure.persistence.models.pause_log_model import PauseLogModel

class PauseLogRepositoryImpl(PauseLogRepository):
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, pause_log: PauseLog) -> PauseLog:
        db_pause = PauseLogModel(
            session_id=pause_log.session_id,
            pause_type=pause_log.pause_type
        )
        self.db.add(db_pause)
        self.db.commit()
        self.db.refresh(db_pause)
        return self._to_domain(db_pause)

    def update(self, pause_log: PauseLog) -> PauseLog:
        db_pause = self.db.query(PauseLogModel).filter(
            PauseLogModel.id == pause_log.id
        ).first()
        if db_pause:
            db_pause.ended_at = pause_log.ended_at
            self.db.commit()
            self.db.refresh(db_pause)
            return self._to_domain(db_pause)
        return pause_log

    def get_active_pause(self, session_id: str) -> Optional[PauseLog]:
        db_pause = self.db.query(PauseLogModel).filter(
            PauseLogModel.session_id == uuid.UUID(session_id),
            PauseLogModel.ended_at.is_(None)
        ).first()
        return self._to_domain(db_pause) if db_pause else None

    @staticmethod
    def _to_domain(db_pause: PauseLogModel) -> PauseLog:
        return PauseLog(
            id=db_pause.id,
            session_id=db_pause.session_id,
            pause_type=db_pause.pause_type,
            started_at=db_pause.started_at,
            ended_at=db_pause.ended_at
        )