from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.api_key import ApiKey

class ApiKeyRepository(ABC):
    @abstractmethod
    def create(self, api_key: ApiKey) -> ApiKey:
        pass

    @abstractmethod
    def get_by_id(self, api_key_id: str) -> Optional[ApiKey]:
        pass

    @abstractmethod
    def get_by_key_value(self, key_value: str) -> Optional[ApiKey]:
        pass

    @abstractmethod
    def get_by_company_id(self, company_id: str) -> List[ApiKey]:
        pass

    @abstractmethod
    def get_by_application_id(self, application_id: str) -> List[ApiKey]:
        pass

    @abstractmethod
    def update(self, api_key: ApiKey) -> ApiKey:
        pass

    @abstractmethod
    def revoke_by_key_value(self, key_value: str) -> bool:
        pass

    @abstractmethod
    def revoke_all_by_company(self, company_id: str) -> int:
        pass