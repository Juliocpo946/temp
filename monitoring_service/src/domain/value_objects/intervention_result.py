from enum import Enum

class InterventionResult(Enum):
    PENDING = "pending"
    IMPROVED = "improved"
    NO_CHANGE = "no_change"
    WORSENED = "worsened"