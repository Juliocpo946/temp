from typing import Dict, Any


class RecommendationDTO:
    def __init__(
        self,
        session_id: str,
        user_id: int,
        action: str,
        content: Dict[str, Any],
        vibration: Dict[str, Any],
        metadata: Dict[str, Any],
        timestamp: int
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.action = action
        self.content = content
        self.vibration = vibration
        self.metadata = metadata
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "action": self.action,
            "content": self.content,
            "vibration": self.vibration,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }