from enum import Enum

class CognitiveState(Enum):
    CONFUSED = 0
    NEUTRAL = 1
    UNDERSTANDING = 2
    
    @classmethod
    def from_string(cls, state: str):
        mapping = {
            "confundido": cls.CONFUSED,
            "neutral": cls.NEUTRAL,
            "entendiendo": cls.UNDERSTANDING
        }
        return mapping.get(state.lower(), cls.NEUTRAL)
    
    def to_float(self) -> float:
        return float(self.value) / 2.0