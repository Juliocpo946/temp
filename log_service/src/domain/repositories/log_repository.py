from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.log import Log

class LogRepository(ABC):
    @abstractmethod
    def save(self, log: Log) -> Log:
        pass

    @abstractmethod
    def get_by_id(self, log_id: str) -> Optional[Log]:
        pass

    @abstractmethod
    def get_by_service(self, service: str, limit: int = 100) -> List[Log]:
        pass

    @abstractmethod
    def get_by_level(self, level: str, limit: int = 100) -> List[Log]:
        pass

    @abstractmethod
    def get_all(self, limit: int = 100) -> List[Log]:
        pass

    @abstractmethod
    def get_by_service_and_level(self, service: str, level: str, limit: int = 100) -> List[Log]:
        pass