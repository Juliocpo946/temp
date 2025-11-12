from typing import Optional
from sqlalchemy.orm import Session as DBSession
import uuid
from src.domain.entities.analysis_config import AnalysisConfig
from src.domain.repositories.analysis_config_repository import AnalysisConfigRepository
from src.infrastructure.persistence.models.analysis_config_model import AnalysisConfigModel

class AnalysisConfigRepositoryImpl(AnalysisConfigRepository):
    def __init__(self, db: DBSession):
        self.db = db

    def create(self, config: AnalysisConfig) -> AnalysisConfig:
        db_config = AnalysisConfigModel(
            session_id=config.session_id,
            cognitive_analysis_enabled=config.cognitive_analysis_enabled,
            text_notifications=config.text_notifications,
            video_suggestions=config.video_suggestions,
            vibration_alerts=config.vibration_alerts,
            pause_suggestions=config.pause_suggestions
        )
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        return self._to_domain(db_config)

    def get_by_session_id(self, session_id: str) -> Optional[AnalysisConfig]:
        db_config = self.db.query(AnalysisConfigModel).filter(
            AnalysisConfigModel.session_id == uuid.UUID(session_id)
        ).first()
        return self._to_domain(db_config) if db_config else None

    def update(self, config: AnalysisConfig) -> AnalysisConfig:
        db_config = self.db.query(AnalysisConfigModel).filter(
            AnalysisConfigModel.id == config.id
        ).first()
        if db_config:
            db_config.cognitive_analysis_enabled = config.cognitive_analysis_enabled
            db_config.text_notifications = config.text_notifications
            db_config.video_suggestions = config.video_suggestions
            db_config.vibration_alerts = config.vibration_alerts
            db_config.pause_suggestions = config.pause_suggestions
            self.db.commit()
            self.db.refresh(db_config)
            return self._to_domain(db_config)
        return config

    @staticmethod
    def _to_domain(db_config: AnalysisConfigModel) -> AnalysisConfig:
        return AnalysisConfig(
            id=db_config.id,
            session_id=db_config.session_id,
            cognitive_analysis_enabled=db_config.cognitive_analysis_enabled,
            text_notifications=db_config.text_notifications,
            video_suggestions=db_config.video_suggestions,
            vibration_alerts=db_config.vibration_alerts,
            pause_suggestions=db_config.pause_suggestions
        )