from typing import List
import numpy as np
from src.application.dtos.biometric_frame_dto import BiometricFrameDTO
from src.infrastructure.config.settings import TEMPORAL_WINDOWS
from src.infrastructure.ml.feature_buffer import FeatureBuffer

class TemporalFeatureExtractor:
    PITCH_MAX = 45.0
    YAW_MAX = 45.0
    
    def __init__(self):
        self.internal_buffer = FeatureBuffer(max_length=max(TEMPORAL_WINDOWS) + 10)
        self.windows = TEMPORAL_WINDOWS

    def extract(self, frame: BiometricFrameDTO) -> np.ndarray:
        base_features = self._extract_base_features(frame)
        self.internal_buffer.add(base_features, frame.to_dict())
        
        if len(self.internal_buffer) < min(self.windows):
            return base_features
        
        all_features = [base_features]
        
        for window_size in self.windows:
            if len(self.internal_buffer) >= window_size:
                window_features = self._extract_window_features(window_size)
                all_features.append(window_features)
        
        return np.concatenate(all_features)

    def _extract_base_features(self, frame: BiometricFrameDTO) -> np.ndarray:
        features = np.zeros(13, dtype=np.float32)
        
        features[0] = frame.get_emotion_value("happiness")
        features[1] = frame.get_emotion_value("neutral")
        features[2] = frame.get_emotion_value("surprise")
        features[3] = frame.get_emotion_value("anger")
        features[4] = frame.get_emotion_value("contempt")
        features[5] = frame.get_emotion_value("disgust")
        features[6] = frame.get_emotion_value("fear")
        features[7] = frame.get_emotion_value("sadness")
        
        features[8] = 1.0 if frame.atencion.get("mirando_pantalla", False) else 0.0
        
        orientacion = frame.atencion.get("orientacion_cabeza", {})
        pitch = orientacion.get("pitch", 0.0)
        yaw = orientacion.get("yaw", 0.0)
        features[9] = np.clip(pitch / self.PITCH_MAX, -1.0, 1.0)
        features[10] = np.clip(yaw / self.YAW_MAX, -1.0, 1.0)
        
        features[11] = 1.0 if frame.somnolencia.get("esta_durmiendo", False) else 0.0
        features[12] = frame.somnolencia.get("apertura_ojos_ear", 0.3)
        
        return features

    def _extract_window_features(self, window_size: int) -> np.ndarray:
        recent = self.internal_buffer.get_recent_features(window_size)
        if recent is None:
            return np.zeros(5, dtype=np.float32)
        
        features = []
        
        negative_emotions = recent[:, [3, 4, 5, 6, 7]]
        avg_negative = np.mean(negative_emotions)
        std_negative = np.std(negative_emotions)
        
        attention = recent[:, 8]
        avg_attention = np.mean(attention)
        
        if len(recent) > 1:
            negative_trend = negative_emotions[-1].mean() - negative_emotions[0].mean()
            attention_trend = attention[-1] - attention[0]
        else:
            negative_trend = 0.0
            attention_trend = 0.0
        
        features.extend([avg_negative, std_negative, avg_attention, negative_trend, attention_trend])
        
        return np.array(features, dtype=np.float32)

    def get_feature_dimension(self) -> int:
        base_dim = 13
        window_dim = 5 * len(self.windows)
        return base_dim + window_dim

    def reset(self) -> None:
        self.internal_buffer.clear()