from enum import Enum

class RecommendationAction(str, Enum):
    INSTRUCCION = "instruccion"
    MOTIVACION = "motivacion"
    PAUSA = "pausa"
    DISTRACCION = "distraccion"
    NADA = "nada"

    @staticmethod
    def is_valid(action: str) -> bool:
        return action in [item.value for item in RecommendationAction]