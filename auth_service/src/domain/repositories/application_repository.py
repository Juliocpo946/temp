from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.application import Application

class ApplicationRepository(ABC):
    @abstractmethod
    def create(self, application: Application) -> Application:
        pass

    @abstractmethod
    def get_by_id(self, application_id: str) -> Optional[Application]:
        pass

    @abstractmethod
    def get_by_company_id(self, company_id: str) -> List[Application]:
        pass

    @abstractmethod
    def update(self, application: Application) -> Application:
        pass

    @abstractmethod
    def delete(self, application_id: str) -> bool:
        pass