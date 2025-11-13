from abc import ABC, abstractmethod
from typing import Optional

class ContentRepository(ABC):
    @abstractmethod
    async def search_specific(
        self,
        recommendation_type: str,
        title: str,
        subtitle: str,
        activity_type: str,
        precision_range: tuple,
        evento: str
    ) -> Optional[dict]:
        pass

    @abstractmethod
    async def search_generic(
        self,
        recommendation_type: str,
        activity_type: str,
        precision_range: tuple,
        evento: str
    ) -> Optional[dict]:
        pass