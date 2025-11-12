from src.domain.repositories.analysis_config_repository import AnalysisConfigRepository

class UpdateConfigUseCase:
    def __init__(self, config_repo: AnalysisConfigRepository):
        self.config_repo = config_repo

    def execute(
        self,
        session_id: str,
        cognitive_analysis_enabled: bool,
        text_notifications: bool,
        video_suggestions: bool,
        vibration_alerts: bool,
        pause_suggestions: bool
    ) -> dict:
        config = self.config_repo.get_by_session_id(session_id)
        if not config:
            raise ValueError("Config not found")

        config.cognitive_analysis_enabled = cognitive_analysis_enabled
        config.text_notifications = text_notifications
        config.video_suggestions = video_suggestions
        config.vibration_alerts = vibration_alerts
        config.pause_suggestions = pause_suggestions

        self.config_repo.update(config)

        return {'status': 'configuracion_actualizada'}