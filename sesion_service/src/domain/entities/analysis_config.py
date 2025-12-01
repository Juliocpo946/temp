from typing import Optional
import uuid

class AnalysisConfig:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        session_id: uuid.UUID,
        cognitive_analysis_enabled: bool,
        text_notifications: bool,
        video_suggestions: bool,
        vibration_alerts: bool,
        pause_suggestions: bool
    ):
        self.id = id or uuid.uuid4()
        self.session_id = session_id
        self.cognitive_analysis_enabled = cognitive_analysis_enabled
        self.text_notifications = text_notifications
        self.video_suggestions = video_suggestions
        self.vibration_alerts = vibration_alerts
        self.pause_suggestions = pause_suggestions

    def update(
        self,
        cognitive_analysis_enabled: bool,
        text_notifications: bool,
        video_suggestions: bool,
        vibration_alerts: bool,
        pause_suggestions: bool
    ) -> None:
        self.cognitive_analysis_enabled = cognitive_analysis_enabled
        self.text_notifications = text_notifications
        self.video_suggestions = video_suggestions
        self.vibration_alerts = vibration_alerts
        self.pause_suggestions = pause_suggestions