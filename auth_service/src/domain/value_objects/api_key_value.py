import secrets
from typing import Optional

class ApiKeyValue:
    def __init__(self, value: Optional[str] = None):
        self.value = value or self._generate()

    @staticmethod
    def _generate() -> str:
        return secrets.token_urlsafe(128)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, ApiKeyValue):
            return self.value == other.value
        return self.value == other