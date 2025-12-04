from enum import Enum

class DecisionReason(Enum):
    STATE_DURATION = "state_duration"
    STATE_SEVERITY = "state_severity"
    TRAJECTORY_PATTERN = "trajectory_pattern"
    EFFECTIVENESS_HISTORY = "effectiveness_history"
    COOLDOWN_ACTIVE = "cooldown_active"
    CLUSTER_CONFIDENCE = "cluster_confidence"
    USER_PATTERN_MATCH = "user_pattern_match"
    EMERGENCY_OVERRIDE = "emergency_override"
    
    def to_string(self) -> str:
        return self.value