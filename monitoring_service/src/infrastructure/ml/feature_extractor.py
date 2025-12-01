from typing import List
import numpy as np
from src.application.dtos.biometric_frame_dto import BiometricFrameDTO
from src.domain.value_objects.cognitive_state import CognitiveState

class FeatureExtractor:
    PITCH_MAX = 45.0
    YAW_MAX = 45.0
    
    def extract(self, frame: BiometricFrameDTO) -> np.ndarray:
        features = np.zeros(16, dtype=np.float32)
        
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
        
        features[13] = 1.0 if frame.rostro_detectado else 0.0
        
        estado = frame.emocion_principal.get("estado_cognitivo", "neutral")
        features[14] = CognitiveState.from_string(estado).to_float()
        
        features[15] = frame.emocion_principal.get("confianza", 0.5)
        
        return features

    def extract_batch(self, frames: List[BiometricFrameDTO]) -> np.ndarray:
        return np.array([self.extract(f) for f in frames], dtype=np.float32)