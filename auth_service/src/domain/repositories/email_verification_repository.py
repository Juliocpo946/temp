from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.email_verification import EmailVerification

class EmailVerificationRepository(ABC):
    @abstractmethod
    def create(self, email_verification: EmailVerification) -> EmailVerification:
        pass

    @abstractmethod
    def get_by_code(self, verification_code: str) -> Optional[EmailVerification]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[EmailVerification]:
        pass

    @abstractmethod
    def update(self, email_verification: EmailVerification) -> EmailVerification:
        pass