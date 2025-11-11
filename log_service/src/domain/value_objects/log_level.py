from enum import Enum

class LogLevel(str, Enum):
    INFO = "info"
    ERROR = "error"
    WARNING = "warning"
    DEBUG = "debug"

    @staticmethod
    def is_valid(level: str) -> bool:
        return level in [item.value for item in LogLevel]