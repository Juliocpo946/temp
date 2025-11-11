from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.company import Company

class CompanyRepository(ABC):
    @abstractmethod
    def create(self, company: Company) -> Company:
        pass

    @abstractmethod
    def get_by_id(self, company_id: int) -> Optional[Company]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Company]:
        pass

    @abstractmethod
    def update(self, company: Company) -> Company:
        pass

    @abstractmethod
    def delete(self, company_id: int) -> bool:
        pass
