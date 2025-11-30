from typing import List, Optional
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session as DBSession
from src.domain.entities.intervention import Intervention
from src.domain.value_objects.intervention_result import InterventionResult
from src.infrastructure.persistence.repositories.intervention_repository import InterventionRepository
from src.infrastructure.persistence.repositories.training_sample_repository import TrainingSampleRepository
from src.infrastructure.ml.sequence_buffer import SequenceBuffer
from src.infrastructure.config.settings import RESULT_EVALUATION_DELAY_SECONDS

class EvaluateInterventionResultUseCase:
    NEGATIVE_EMOTION_INDICES = [3, 4, 5, 6, 7]
    ATTENTION_INDEX = 8
    FACE_DETECTED_INDEX = 13

    def __init__(self, db: DBSession):
        self.db = db
        self.intervention_repo = InterventionRepository(db)
        self.training_sample_repo = TrainingSampleRepository(db)

    def execute(self, buffer: SequenceBuffer) -> List[str]:
        threshold_time = datetime.utcnow() - timedelta(seconds=RESULT_EVALUATION_DELAY_SECONDS)
        pending_interventions = self.intervention_repo.get_pending_evaluations(threshold_time)

        evaluated_ids = []
        for intervention in pending_interventions:
            result = self._evaluate_single(intervention, buffer)
            if result:
                intervention.evaluate_result(result.value)
                self.intervention_repo.update(intervention)
                self._update_training_sample_label(intervention, result)
                evaluated_ids.append(str(intervention.id))

        return evaluated_ids

    def _evaluate_single(
        self,
        intervention: Intervention,
        buffer: SequenceBuffer
    ) -> Optional[InterventionResult]:
        if not buffer.is_ready():
            return None

        current_frames = buffer.get_recent_frames(10)
        if len(current_frames) < 5:
            return None

        baseline_snapshot = intervention.window_snapshot.get("frames", [])
        if len(baseline_snapshot) < 10:
            return InterventionResult.NO_CHANGE

        baseline_frames = self._extract_features_from_snapshot(baseline_snapshot[-10:])
        
        baseline_negative = self._calculate_negative_emotions(baseline_frames)
        baseline_attention = self._calculate_attention(baseline_frames)
        
        current_negative = self._calculate_negative_emotions(current_frames)
        current_attention = self._calculate_attention(current_frames)

        negative_improved = current_negative < baseline_negative - 0.1
        attention_improved = current_attention > baseline_attention + 0.1
        
        negative_worsened = current_negative > baseline_negative + 0.1
        attention_worsened = current_attention < baseline_attention - 0.1

        if negative_improved or attention_improved:
            return InterventionResult.IMPROVED
        elif negative_worsened and attention_worsened:
            return InterventionResult.WORSENED
        else:
            return InterventionResult.NO_CHANGE

    def _extract_features_from_snapshot(self, snapshot: List[dict]) -> List[np.ndarray]:
        features_list = []
        for frame_data in snapshot:
            features = np.zeros(16, dtype=np.float32)
            
            desglose = frame_data.get("desglose_emociones", [])
            emotion_map = {e.get("emocion", "").lower(): e.get("confianza", 0) / 100.0 for e in desglose}
            
            features[0] = emotion_map.get("happiness", 0)
            features[1] = emotion_map.get("neutral", 0)
            features[2] = emotion_map.get("surprise", 0)
            features[3] = emotion_map.get("anger", 0)
            features[4] = emotion_map.get("contempt", 0)
            features[5] = emotion_map.get("disgust", 0)
            features[6] = emotion_map.get("fear", 0)
            features[7] = emotion_map.get("sadness", 0)
            
            atencion = frame_data.get("atencion", {})
            features[8] = 1.0 if atencion.get("mirando_pantalla", False) else 0.0
            
            features[13] = 1.0 if frame_data.get("rostro_detectado", False) else 0.0
            
            features_list.append(features)
        
        return features_list

    def _calculate_negative_emotions(self, frames: List[np.ndarray]) -> float:
        if not frames:
            return 0.0
        total = 0.0
        for frame in frames:
            for idx in self.NEGATIVE_EMOTION_INDICES:
                total += frame[idx]
        return total / (len(frames) * len(self.NEGATIVE_EMOTION_INDICES))

    def _calculate_attention(self, frames: List[np.ndarray]) -> float:
        if not frames:
            return 0.0
        attention_sum = sum(frame[self.ATTENTION_INDEX] for frame in frames)
        face_sum = sum(frame[self.FACE_DETECTED_INDEX] for frame in frames)
        return (attention_sum + face_sum) / (2 * len(frames))

    def _update_training_sample_label(
        self,
        intervention: Intervention,
        result: InterventionResult
    ) -> None:
        sample = self.training_sample_repo.get_by_intervention_id(str(intervention.id))
        if not sample:
            return

        if result == InterventionResult.WORSENED:
            self.training_sample_repo.update_label(str(sample.id), 0)