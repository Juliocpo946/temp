from datetime import datetime
from typing import Optional


class Content:
    def __init__(
        self,
        id: Optional[int],
        topic: str,
        subtopic: Optional[str],
        activity_type: Optional[str],
        intervention_type: str,
        content: str,
        active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.topic = topic
        self.subtopic = subtopic
        self.activity_type = activity_type
        self.intervention_type = intervention_type
        self.content = content
        self.active = active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def update(
        self,
        topic: Optional[str] = None,
        subtopic: Optional[str] = None,
        activity_type: Optional[str] = None,
        intervention_type: Optional[str] = None,
        content: Optional[str] = None,
        active: Optional[bool] = None
    ) -> None:
        if topic is not None:
            self.topic = topic
        if subtopic is not None:
            self.subtopic = subtopic
        if activity_type is not None:
            self.activity_type = activity_type
        if intervention_type is not None:
            self.intervention_type = intervention_type
        if content is not None:
            self.content = content
        if active is not None:
            self.active = active
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "activity_type": self.activity_type,
            "intervention_type": self.intervention_type,
            "content": self.content,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }