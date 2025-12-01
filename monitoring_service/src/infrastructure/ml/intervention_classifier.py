from typing import Tuple, Optional
import numpy as np
from src.infrastructure.ml.model_loader import ModelLoader
from src.infrastructure.ml.sequence_buffer import SequenceBuffer
from src.infrastructure.config.settings import CONFIDENCE_THRESHOLD
from src.domain.value_objects.intervention_type import InterventionType

class InterventionClassifier:
    def __init__(self):
        self.model_loader = ModelLoader()

    def classify(
        self,
        sequence: np.ndarray,
        context: np.ndarray
    ) -> Tuple[InterventionType, float]:
        predicted_class, confidence = self.model_loader.predict(sequence, context)
        intervention_type = InterventionType.from_prediction(predicted_class)
        return intervention_type, confidence

    def should_intervene(
        self,
        intervention_type: InterventionType,
        confidence: float
    ) -> bool:
        if intervention_type == InterventionType.NO_INTERVENTION:
            return False
        return confidence >= CONFIDENCE_THRESHOLD