from enum import Enum


class InterventionType(str, Enum):
    VIBRATION = "vibration"
    INSTRUCTION = "instruction"
    PAUSE = "pause"