from typing import Dict, Any, Optional


class ActivityDetailsRequestDTO:
    def __init__(
        self,
        activity_uuid: str,
        correlation_id: str
    ):
        self.activity_uuid = activity_uuid
        self.correlation_id = correlation_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "activity_details_request",
            "activity_uuid": self.activity_uuid,
            "correlation_id": self.correlation_id
        }


class ActivityDetailsResponseDTO:
    def __init__(
        self,
        activity_uuid: str,
        title: str,
        subtitle: Optional[str],
        content: Optional[str],
        activity_type: str,
        correlation_id: str
    ):
        self.activity_uuid = activity_uuid
        self.title = title
        self.subtitle = subtitle
        self.content = content
        self.activity_type = activity_type
        self.correlation_id = correlation_id

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActivityDetailsResponseDTO":
        return cls(
            activity_uuid=data.get("activity_uuid"),
            title=data.get("title"),
            subtitle=data.get("subtitle"),
            content=data.get("content"),
            activity_type=data.get("activity_type"),
            correlation_id=data.get("correlation_id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_uuid": self.activity_uuid,
            "title": self.title,
            "subtitle": self.subtitle,
            "content": self.content,
            "activity_type": self.activity_type,
            "correlation_id": self.correlation_id
        }