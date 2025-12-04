from typing import List, Dict, Tuple
from collections import Counter
from src.domain.value_objects.cognitive_state import CognitiveState

class PatternAnalyzer:
    def analyze_trajectory(
        self,
        state_history: List[CognitiveState]
    ) -> Dict[str, any]:
        if not state_history:
            return {
                "pattern": "none",
                "severity": 0.0,
                "requires_intervention": False
            }
        
        state_counts = Counter(state_history)
        most_common_state = state_counts.most_common(1)[0][0]
        
        severity = self._calculate_severity(state_history)
        pattern = self._detect_pattern(state_history)
        requires_intervention = self._requires_intervention(state_history, severity)
        
        return {
            "pattern": pattern,
            "dominant_state": most_common_state.to_string(),
            "severity": severity,
            "requires_intervention": requires_intervention,
            "state_distribution": {s.to_string(): c for s, c in state_counts.items()}
        }

    def _calculate_severity(self, state_history: List[CognitiveState]) -> float:
        severity_map = {
            CognitiveState.INITIALIZING: 0.0,
            CognitiveState.ENGAGED: 0.0,
            CognitiveState.LIGHT_DISTRACTION: 0.3,
            CognitiveState.HEAVY_DISTRACTION: 0.6,
            CognitiveState.CONFUSION: 0.5,
            CognitiveState.FRUSTRATION: 0.7,
            CognitiveState.COGNITIVE_OVERLOAD: 0.9,
            CognitiveState.FATIGUE: 0.8
        }
        
        severities = [severity_map.get(s, 0.0) for s in state_history]
        return sum(severities) / len(severities) if severities else 0.0

    def _detect_pattern(self, state_history: List[CognitiveState]) -> str:
        if len(state_history) < 3:
            return "insufficient_data"
        
        last_three = state_history[-3:]
        
        if all(s == last_three[0] for s in last_three):
            return "stable"
        
        negative_states = {
            CognitiveState.HEAVY_DISTRACTION,
            CognitiveState.FRUSTRATION,
            CognitiveState.COGNITIVE_OVERLOAD
        }
        
        if all(s in negative_states for s in last_three):
            return "deteriorating"
        
        if last_three[0] in negative_states and last_three[-1] == CognitiveState.ENGAGED:
            return "recovering"
        
        return "fluctuating"

    def _requires_intervention(
        self,
        state_history: List[CognitiveState],
        severity: float
    ) -> bool:
        if severity >= 0.7:
            return True
        
        if len(state_history) < 5:
            return False
        
        recent = state_history[-5:]
        critical_states = {
            CognitiveState.COGNITIVE_OVERLOAD,
            CognitiveState.FRUSTRATION
        }
        
        critical_count = sum(1 for s in recent if s in critical_states)
        return critical_count >= 3

    def detect_state_transition(
        self,
        previous_state: CognitiveState,
        current_state: CognitiveState
    ) -> Tuple[bool, str]:
        if previous_state == current_state:
            return False, "no_change"
        
        positive_transitions = {
            (CognitiveState.FRUSTRATION, CognitiveState.ENGAGED),
            (CognitiveState.CONFUSION, CognitiveState.ENGAGED),
            (CognitiveState.HEAVY_DISTRACTION, CognitiveState.LIGHT_DISTRACTION),
            (CognitiveState.COGNITIVE_OVERLOAD, CognitiveState.CONFUSION)
        }
        
        negative_transitions = {
            (CognitiveState.ENGAGED, CognitiveState.FRUSTRATION),
            (CognitiveState.CONFUSION, CognitiveState.COGNITIVE_OVERLOAD),
            (CognitiveState.LIGHT_DISTRACTION, CognitiveState.HEAVY_DISTRACTION)
        }
        
        transition = (previous_state, current_state)
        
        if transition in positive_transitions:
            return True, "improvement"
        elif transition in negative_transitions:
            return True, "deterioration"
        else:
            return True, "neutral_change"