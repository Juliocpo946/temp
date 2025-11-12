from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.activity_log import ActivityLog

class ActivityLogRepository(ABC):
    @abstractmethod
    def create(self, activity_log: ActivityLog) -> ActivityLog:
        pass

    @abstractmethod
    def get_by_session_id(self, session_id: str) -> List[ActivityLog]:
        pass

    @abstractmethod
    def update(self, activity_log: ActivityLog) -> ActivityLog:
        pass