from enum import Enum

class InterventionResult(Enum):
    PENDING = "pending"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NO_EFFECT = "no_effect"