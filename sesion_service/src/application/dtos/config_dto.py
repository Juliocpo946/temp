class ConfigDTO:
    def __init__(
        self,
        session_id: str,
        cognitive_analysis_enabled: bool,
        text_notifications: bool,
        video_suggestions: bool,
        vibration_alerts: bool,
        pause_suggestions: bool
    ):
        self.session_id = session_id
        self.cognitive_analysis_enabled = cognitive_analysis_enabled
        self.text_notifications = text_notifications
        self.video_suggestions = video_suggestions
        self.vibration_alerts = vibration_alerts
        self.pause_suggestions = pause_suggestions

    def to_dict(self) -> dict:
        return {
            'session_id': str(self.session_id),
            'cognitive_analysis_enabled': self.cognitive_analysis_enabled,
            'text_notifications': self.text_notifications,
            'video_suggestions': self.video_suggestions,
            'vibration_alerts': self.vibration_alerts,
            'pause_suggestions': self.pause_suggestions
        }