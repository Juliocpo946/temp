from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.session import Session

class SessionRepository(ABC):
    @abstractmethod
    def create(self, session: Session) -> Session:
        pass

    @abstractmethod
    def get_by_id(self, session_id: str) -> Optional[Session]:
        pass

    @abstractmethod
    def update(self, session: Session) -> Session:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Session]:
        pass

    @abstractmethod
    def delete_old_sessions(self, hours: int) -> int:
        pass