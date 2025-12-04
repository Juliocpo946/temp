from typing import Optional, Tuple
from datetime import datetime, timedelta
from src.domain.value_objects.cognitive_state import CognitiveState
from src.domain.value_objects.intervention_type import InterventionType
from src.domain.value_objects.decision_reason import DecisionReason
from src.infrastructure.config.settings import DECISION_CONFIDENCE_THRESHOLD

class InterventionPolicy:
    def __init__(self):
        self.state_duration_thresholds = {
            CognitiveState.HEAVY_DISTRACTION: 20,
            CognitiveState.CONFUSION: 30,
            CognitiveState.FRUSTRATION: 25,
            CognitiveState.COGNITIVE_OVERLOAD: 10,
            CognitiveState.FATIGUE: 120
        }

    def evaluate(
        self,
        current_state: CognitiveState,
        state_duration: int,
        trajectory: list,
        decision_score: float,
        intervention_counts: dict,
        effectiveness_history: dict
    ) -> Tuple[bool, Optional[InterventionType], DecisionReason, float]:
        
        if current_state == CognitiveState.INITIALIZING:
            return False, None, DecisionReason.CLUSTER_CONFIDENCE, 0.0
        
        if current_state == CognitiveState.ENGAGED:
            return False, None, DecisionReason.STATE_DURATION, 1.0
        
        if decision_score < DECISION_CONFIDENCE_THRESHOLD:
            return False, None, DecisionReason.CLUSTER_CONFIDENCE, decision_score
        
        threshold = self.state_duration_thresholds.get(current_state, 30)
        if state_duration < threshold:
            return False, None, DecisionReason.STATE_DURATION, decision_score
        
        intervention_type = self._determine_intervention_type(
            current_state,
            state_duration,
            trajectory,
            intervention_counts,
            effectiveness_history
        )
        
        if intervention_type == InterventionType.NO_INTERVENTION:
            return False, None, DecisionReason.STATE_SEVERITY, decision_score
        
        reason = self._determine_reason(current_state, intervention_type)
        
        return True, intervention_type, reason, decision_score

    def _determine_intervention_type(
        self,
        state: CognitiveState,
        duration: int,
        trajectory: list,
        intervention_counts: dict,
        effectiveness_history: dict
    ) -> InterventionType:
        
        if state == CognitiveState.COGNITIVE_OVERLOAD:
            return InterventionType.PAUSE
        
        if state == CognitiveState.FATIGUE and duration > 120:
            return InterventionType.PAUSE
        
        if state == CognitiveState.FRUSTRATION:
            instruction_count = intervention_counts.get("instruction", 0)
            instruction_effectiveness = effectiveness_history.get("instruction", 0.5)
            
            if instruction_count == 0:
                return InterventionType.INSTRUCTION
            elif instruction_count >= 1 and instruction_effectiveness < 0.4:
                return InterventionType.PAUSE
            elif instruction_count >= 2:
                return InterventionType.PAUSE
            else:
                return InterventionType.INSTRUCTION
        
        if state == CognitiveState.CONFUSION:
            instruction_count = intervention_counts.get("instruction", 0)
            if instruction_count < 2:
                return InterventionType.INSTRUCTION
            else:
                return InterventionType.PAUSE
        
        if state == CognitiveState.HEAVY_DISTRACTION:
            vibration_count = intervention_counts.get("vibration", 0)
            vibration_effectiveness = effectiveness_history.get("vibration", 0.5)
            
            if vibration_count >= 2 and vibration_effectiveness < 0.5:
                return InterventionType.PAUSE
            else:
                return InterventionType.VIBRATION
        
        if state == CognitiveState.LIGHT_DISTRACTION:
            if duration > 40:
                return InterventionType.VIBRATION
        
        return InterventionType.NO_INTERVENTION

    def _determine_reason(
        self,
        state: CognitiveState,
        intervention_type: InterventionType
    ) -> DecisionReason:
        
        if intervention_type == InterventionType.PAUSE:
            return DecisionReason.STATE_SEVERITY
        
        if state in [CognitiveState.FRUSTRATION, CognitiveState.CONFUSION]:
            return DecisionReason.TRAJECTORY_PATTERN
        
        if state in [CognitiveState.HEAVY_DISTRACTION, CognitiveState.LIGHT_DISTRACTION]:
            return DecisionReason.STATE_DURATION
        
        return DecisionReason.STATE_SEVERITY