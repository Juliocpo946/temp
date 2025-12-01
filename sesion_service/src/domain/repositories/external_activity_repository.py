from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.external_activity import ExternalActivity

class ExternalActivityRepository(ABC):
    @abstractmethod
    def create(self, activity: ExternalActivity) -> ExternalActivity:
        pass

    @abstractmethod
    def get_by_external_id(self, external_activity_id: int) -> Optional[ExternalActivity]:
        pass

    @abstractmethod
    def get_or_create(
        self,
        external_activity_id: int,
        title: str,
        subtitle: Optional[str],
        content: Optional[str],
        activity_type: str
    ) -> ExternalActivity:
        pass