from typing import Dict, List
import numpy as np
from src.domain.value_objects.cognitive_state import CognitiveState

class EffectivenessTracker:
    def calculate_effectiveness(
        self,
        intervention_type: str,
        pre_state: CognitiveState,
        post_state: CognitiveState,
        pre_features: np.ndarray,
        post_features: np.ndarray
    ) -> float:
        
        state_improvement = self._calculate_state_improvement(pre_state, post_state)
        
        feature_improvement = self._calculate_feature_improvement(
            pre_features,
            post_features,
            intervention_type
        )
        
        effectiveness = (state_improvement * 0.6) + (feature_improvement * 0.4)
        
        return np.clip(effectiveness, 0.0, 1.0)

    def _calculate_state_improvement(
        self,
        pre_state: CognitiveState,
        post_state: CognitiveState
    ) -> float:
        
        state_scores = {
            CognitiveState.COGNITIVE_OVERLOAD: 0.0,
            CognitiveState.FATIGUE: 0.1,
            CognitiveState.FRUSTRATION: 0.2,
            CognitiveState.HEAVY_DISTRACTION: 0.3,
            CognitiveState.CONFUSION: 0.4,
            CognitiveState.LIGHT_DISTRACTION: 0.6,
            CognitiveState.ENGAGED: 1.0,
            CognitiveState.INITIALIZING: 0.5
        }
        
        pre_score = state_scores.get(pre_state, 0.5)
        post_score = state_scores.get(post_state, 0.5)
        
        improvement = post_score - pre_score
        
        return np.clip((improvement + 1.0) / 2.0, 0.0, 1.0)

    def _calculate_feature_improvement(
        self,
        pre_features: np.ndarray,
        post_features: np.ndarray,
        intervention_type: str
    ) -> float:
        
        if intervention_type == "vibration":
            return self._calculate_attention_improvement(pre_features, post_features)
        elif intervention_type == "instruction":
            return self._calculate_frustration_improvement(pre_features, post_features)
        elif intervention_type == "pause":
            return self._calculate_overall_improvement(pre_features, post_features)
        
        return 0.5

    def _calculate_attention_improvement(
        self,
        pre_features: np.ndarray,
        post_features: np.ndarray
    ) -> float:
        
        pre_attention = pre_features[8] if len(pre_features) > 8 else 0.5
        post_attention = post_features[8] if len(post_features) > 8 else 0.5
        
        improvement = post_attention - pre_attention
        return np.clip((improvement + 1.0) / 2.0, 0.0, 1.0)

    def _calculate_frustration_improvement(
        self,
        pre_features: np.ndarray,
        post_features: np.ndarray
    ) -> float:
        
        negative_indices = [3, 4, 5, 6, 7]
        
        pre_negative = np.mean([pre_features[i] for i in negative_indices if i < len(pre_features)])
        post_negative = np.mean([post_features[i] for i in negative_indices if i < len(post_features)])
        
        reduction = pre_negative - post_negative
        return np.clip((reduction + 1.0) / 2.0, 0.0, 1.0)

    def _calculate_overall_improvement(
        self,
        pre_features: np.ndarray,
        post_features: np.ndarray
    ) -> float:
        
        attention_improvement = self._calculate_attention_improvement(pre_features, post_features)
        frustration_improvement = self._calculate_frustration_improvement(pre_features, post_features)
        
        return (attention_improvement + frustration_improvement) / 2.0