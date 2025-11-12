from abc import ABC, abstractmethod
from src.domain.entities.pause_log import PauseLog

class PauseLogRepository(ABC):
    @abstractmethod
    def create(self, pause_log: PauseLog) -> PauseLog:
        pass

    @abstractmethod
    def update(self, pause_log: PauseLog) -> PauseLog:
        pass

    @abstractmethod
    def get_active_pause(self, session_id: str):
        pass