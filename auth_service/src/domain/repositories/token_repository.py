from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.token import Token

class TokenRepository(ABC):
    @abstractmethod
    def create(self, token: Token) -> Token:
        pass

    @abstractmethod
    def get_by_id(self, token_id: str) -> Optional[Token]:
        pass

    @abstractmethod
    def get_by_token(self, token_value: str) -> Optional[Token]:
        pass

    @abstractmethod
    def get_by_company_id(self, company_id: int) -> list[Token]:
        pass

    @abstractmethod
    def update(self, token: Token) -> Token:
        pass

    @abstractmethod
    def revoke_by_token(self, token_value: str) -> bool:
        pass

    @abstractmethod
    def revoke_all_by_company(self, company_id: int) -> int:
        pass