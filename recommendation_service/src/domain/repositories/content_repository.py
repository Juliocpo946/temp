from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.content import Content


class ContentRepository(ABC):
    @abstractmethod
    def save(self, content: Content) -> Content:
        pass

    @abstractmethod
    def get_by_id(self, content_id: int) -> Optional[Content]:
        pass

    @abstractmethod
    def find_by_criteria(
        self,
        topic: str,
        intervention_type: str,
        subtopic: Optional[str] = None,
        activity_type: Optional[str] = None
    ) -> Optional[Content]:
        pass

    @abstractmethod
    def list_all(
        self,
        topic: Optional[str] = None,
        subtopic: Optional[str] = None,
        activity_type: Optional[str] = None,
        intervention_type: Optional[str] = None,
        active: Optional[bool] = None
    ) -> List[Content]:
        pass

    @abstractmethod
    def update(self, content: Content) -> Content:
        pass

    @abstractmethod
    def delete(self, content_id: int) -> bool:
        pass