from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.payment import Payment

class PaymentRepository(ABC):
    @abstractmethod
    def create(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    def get_by_external_id(self, external_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def get_by_application_id(self, application_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def update(self, payment: Payment) -> Payment:
        pass