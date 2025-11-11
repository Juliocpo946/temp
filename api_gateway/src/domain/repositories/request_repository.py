from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.request import Request

class RequestRepository(ABC):
    @abstractmethod
    def log_request(self, request: Request) -> None:
        pass

    @abstractmethod
    def get_by_correlation_id(self, correlation_id: str) -> Optional[Request]:
        pass