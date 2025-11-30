from datetime import datetime
from typing import Optional
import uuid

class ExternalActivity:
    def __init__(
        self,
        id: Optional[uuid.UUID],
        external_activity_id: int,
        title: str,
        subtitle: Optional[str],
        content: Optional[str],
        activity_type: str
    ):
        self.id = id or uuid.uuid4()
        self.external_activity_id = external_activity_id
        self.title = title
        self.subtitle = subtitle
        self.content = content
        self.activity_type = activity_type