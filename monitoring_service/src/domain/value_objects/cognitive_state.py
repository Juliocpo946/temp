from enum import Enum

class CognitiveState(Enum):
    INITIALIZING = "initializing"
    ENGAGED = "engaged"
    LIGHT_DISTRACTION = "light_distraction"
    HEAVY_DISTRACTION = "heavy_distraction"
    CONFUSION = "confusion"
    FRUSTRATION = "frustration"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    FATIGUE = "fatigue"
    
    @classmethod
    def from_string(cls, state: str):
        mapping = {
            "initializing": cls.INITIALIZING,
            "engaged": cls.ENGAGED,
            "light_distraction": cls.LIGHT_DISTRACTION,
            "heavy_distraction": cls.HEAVY_DISTRACTION,
            "confusion": cls.CONFUSION,
            "frustration": cls.FRUSTRATION,
            "cognitive_overload": cls.COGNITIVE_OVERLOAD,
            "fatigue": cls.FATIGUE
        }
        return mapping.get(state.lower(), cls.ENGAGED)
    
    def to_string(self) -> str:
        return self.value
    
    def requires_intervention(self) -> bool:
        return self in [
            self.HEAVY_DISTRACTION,
            self.CONFUSION,
            self.FRUSTRATION,
            self.COGNITIVE_OVERLOAD,
            self.FATIGUE
        ]