from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.login_attempt import LoginAttempt

class LoginAttemptRepository(ABC):
    @abstractmethod
    def create(self, login_attempt: LoginAttempt) -> LoginAttempt:
        pass

    @abstractmethod
    def get_by_code(self, otp_code: str) -> Optional[LoginAttempt]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[LoginAttempt]:
        pass

    @abstractmethod
    def update(self, login_attempt: LoginAttempt) -> LoginAttempt:
        pass

    @abstractmethod
    def invalidate_previous_codes(self, email: str) -> int:
        pass

    @abstractmethod
    def delete_expired(self) -> int:
        pass

    @abstractmethod
    def count_recent_attempts(self, email: str, minutes: int) -> int:
        pass