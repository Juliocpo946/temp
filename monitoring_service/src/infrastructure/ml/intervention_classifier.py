from typing import Tuple, Optional
import numpy as np
from src.infrastructure.ml.model_loader import ModelLoader
from src.infrastructure.ml.sequence_buffer import SequenceBuffer
from src.infrastructure.config.settings import CONFIDENCE_THRESHOLD
from src.domain.value_objects.intervention_type import InterventionType

class InterventionClassifier:
    def __init__(self):
        self.model_loader = ModelLoader()

    # RENOMBRADO: de classify a predict para coincidir con el caso de uso
    def predict(
        self,
        sequence: np.ndarray,
        context: np.ndarray
    ) -> Tuple[InterventionType, float]:
        try:
            predicted_class, confidence = self.model_loader.predict(sequence, context)
            intervention_type = InterventionType.from_prediction(predicted_class)
            return intervention_type, confidence
        except Exception as e:
            print(f"[CLASSIFIER] [ERROR] Error en prediccion: {e}")
            # En caso de error, fallar seguro a "no intervención"
            return InterventionType.NO_INTERVENTION, 0.0

    def should_intervene(
        self,
        intervention_type: InterventionType,
        confidence: float
    ) -> bool:
        if intervention_type == InterventionType.NO_INTERVENTION:
            return False
        return confidence >= CONFIDENCE_THRESHOLD