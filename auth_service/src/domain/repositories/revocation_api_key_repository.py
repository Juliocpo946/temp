from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.revocation_api_key import RevocationApiKey

class RevocationApiKeyRepository(ABC):
    @abstractmethod
    def create(self, revocation_api_key: RevocationApiKey) -> RevocationApiKey:
        pass

    @abstractmethod
    def get_by_code(self, confirmation_code: str) -> Optional[RevocationApiKey]:
        pass

    @abstractmethod
    def get_by_api_key_id(self, api_key_id: str) -> Optional[RevocationApiKey]:
        pass

    @abstractmethod
    def update(self, revocation_api_key: RevocationApiKey) -> RevocationApiKey:
        pass