from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.revocation_token import RevocationToken

class RevocationTokenRepository(ABC):
    @abstractmethod
    def create(self, revocation_token: RevocationToken) -> RevocationToken:
        pass

    @abstractmethod
    def get_by_code(self, confirmation_code: str) -> Optional[RevocationToken]:
        pass

    @abstractmethod
    def get_by_api_key_id(self, api_key_id: str) -> Optional[RevocationToken]:
        pass

    @abstractmethod
    def update(self, revocation_token: RevocationToken) -> RevocationToken:
        pass