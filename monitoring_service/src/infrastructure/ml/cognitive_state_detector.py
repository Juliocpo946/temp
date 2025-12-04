from typing import Optional, List, Tuple
from collections import deque
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from src.domain.value_objects.cognitive_state import CognitiveState
from src.infrastructure.config.settings import (
    CLUSTERING_MIN_SAMPLES,
    CLUSTERING_UPDATE_FREQUENCY,
    CLUSTERING_MIN_CLUSTER_SIZE
)

class CognitiveStateDetector:
    def __init__(self):
        self.clusterer = MiniBatchKMeans(n_clusters=7, random_state=42, batch_size=100)
        self.feature_history = deque(maxlen=500)
        self.state_history = deque(maxlen=100)
        self.cluster_to_state_map = self._initialize_cluster_map()
        self.frames_since_update = 0
        self.is_initialized = False
        self.feature_dim: Optional[int] = None

    def _initialize_cluster_map(self) -> dict:
        return {
            0: CognitiveState.ENGAGED,
            1: CognitiveState.LIGHT_DISTRACTION,
            2: CognitiveState.HEAVY_DISTRACTION,
            3: CognitiveState.CONFUSION,
            4: CognitiveState.FRUSTRATION,
            5: CognitiveState.COGNITIVE_OVERLOAD,
            6: CognitiveState.FATIGUE
        }

    def detect_state(self, features: np.ndarray) -> Tuple[CognitiveState, float, int]:
        if not isinstance(features, np.ndarray):
            features = np.array(features, dtype=np.float32)
        
        if features.ndim == 2:
            features = features.flatten()
        
        features = features.astype(np.float32)
        
        current_dim = len(features)
        
        if self.feature_dim is None:
            self.feature_dim = current_dim
        elif current_dim != self.feature_dim:
            if current_dim < self.feature_dim:
                padding = np.zeros(self.feature_dim - current_dim, dtype=np.float32)
                features = np.concatenate([features, padding])
            else:
                features = features[:self.feature_dim]
        
        self.feature_history.append(features)
        
        if len(self.feature_history) < CLUSTERING_MIN_SAMPLES:
            self.state_history.append(CognitiveState.INITIALIZING)
            return CognitiveState.INITIALIZING, 0.0, -1
        
        if not self.is_initialized:
            self._initial_fit()
            self.is_initialized = True
        
        self.frames_since_update += 1
        if self.frames_since_update >= CLUSTERING_UPDATE_FREQUENCY:
            self._incremental_update()
            self.frames_since_update = 0
        
        features_2d = features.reshape(1, -1)
        cluster_id = int(self.clusterer.predict(features_2d)[0])
        
        distances = self.clusterer.transform(features_2d)[0]
        confidence = 1.0 / (1.0 + distances[cluster_id])
        
        state = self.cluster_to_state_map.get(cluster_id, CognitiveState.ENGAGED)
        self.state_history.append(state)
        
        return state, confidence, cluster_id

    def _initial_fit(self) -> None:
        try:
            valid_features = [
                vec for vec in self.feature_history
                if isinstance(vec, np.ndarray) and len(vec) == self.feature_dim
            ]
            
            if len(valid_features) < CLUSTERING_MIN_SAMPLES:
                raise ValueError(
                    f"[COGNITIVE_STATE_DETECTOR] [ERROR] Vectores válidos insuficientes: "
                    f"requerido={CLUSTERING_MIN_SAMPLES}, disponible={len(valid_features)}"
                )
            
            features_array = np.stack(valid_features)
            self.clusterer.fit(features_array)
            
        except Exception as e:
            raise RuntimeError(
                f"[COGNITIVE_STATE_DETECTOR] [ERROR] Fallo en ajuste inicial: {str(e)}"
            )

    def _incremental_update(self) -> None:
        try:
            recent_features = list(self.feature_history)[-CLUSTERING_UPDATE_FREQUENCY:]
            valid_features = [
                vec for vec in recent_features
                if isinstance(vec, np.ndarray) and len(vec) == self.feature_dim
            ]
            
            if len(valid_features) < CLUSTERING_UPDATE_FREQUENCY // 2:
                return
            
            features_array = np.stack(valid_features)
            self.clusterer.partial_fit(features_array)
            
        except Exception:
            pass

    def get_state_trajectory(self, window_size: int = 10) -> List[CognitiveState]:
        return list(self.state_history)[-window_size:]

    def is_state_stable(self, min_duration: int = 5) -> bool:
        if len(self.state_history) < min_duration:
            return False
        recent = list(self.state_history)[-min_duration:]
        return len(set(recent)) == 1

    def get_current_state(self) -> Optional[CognitiveState]:
        if not self.state_history:
            return None
        return self.state_history[-1]

    def get_stability_score(self, window_size: int = 10) -> float:
        if len(self.state_history) < window_size:
            return 0.0
        recent = list(self.state_history)[-window_size:]
        most_common = max(set(recent), key=recent.count)
        return recent.count(most_common) / len(recent)

    def reset(self) -> None:
        self.feature_history.clear()
        self.state_history.clear()
        self.frames_since_update = 0
        self.is_initialized = False
        self.feature_dim = None