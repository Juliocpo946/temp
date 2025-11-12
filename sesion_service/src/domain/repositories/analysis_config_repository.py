from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.analysis_config import AnalysisConfig

class AnalysisConfigRepository(ABC):
    @abstractmethod
    def create(self, config: AnalysisConfig) -> AnalysisConfig:
        pass

    @abstractmethod
    def get_by_session_id(self, session_id: str) -> Optional[AnalysisConfig]:
        pass

    @abstractmethod
    def update(self, config: AnalysisConfig) -> AnalysisConfig:
        pass