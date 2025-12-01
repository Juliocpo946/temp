from enum import Enum

class InterventionType(Enum):
    NO_INTERVENTION = 0
    VIBRATION = 1
    INSTRUCTION = 2
    PAUSE = 3
    
    @classmethod
    def from_prediction(cls, prediction: int):
        mapping = {
            0: cls.NO_INTERVENTION,
            1: cls.VIBRATION,
            2: cls.INSTRUCTION,
            3: cls.PAUSE
        }
        return mapping.get(prediction, cls.NO_INTERVENTION)
    
    def to_string(self) -> str:
        mapping = {
            self.NO_INTERVENTION: "no_intervention",
            self.VIBRATION: "vibration",
            self.INSTRUCTION: "instruction",
            self.PAUSE: "pause"
        }
        return mapping.get(self, "no_intervention")