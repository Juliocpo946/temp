from pydantic import BaseModel

class ConfigUpdateSchema(BaseModel):
    cognitive_analysis_enabled: bool
    text_notifications: bool
    video_suggestions: bool
    vibration_alerts: bool
    pause_suggestions: bool