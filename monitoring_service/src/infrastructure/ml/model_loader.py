from typing import Optional
import os
import numpy as np
from src.infrastructure.config.settings import MODEL_PATH, SEQUENCE_LENGTH

class ModelLoader:
    _instance: Optional["ModelLoader"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
            cls._instance._is_loaded = False
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load(self) -> bool:
        try:
            if os.path.exists(MODEL_PATH):
                from tensorflow import keras
                self._model = keras.models.load_model(MODEL_PATH)
                self._is_loaded = True
                print(f"[INFO] Modelo cargado desde {MODEL_PATH}")
                return True
            else:
                print(f"[WARN] Modelo no encontrado en {MODEL_PATH}, usando modo sintetico")
                self._is_loaded = False
                return False
        except Exception as e:
            print(f"[ERROR] Error cargando modelo: {e}")
            self._is_loaded = False
            return False

    def predict(self, sequence: np.ndarray, context: np.ndarray) -> tuple:
        if self._model is not None and self._is_loaded:
            sequence_input = np.expand_dims(sequence, axis=0)
            context_input = np.expand_dims(context, axis=0)
            predictions = self._model.predict([sequence_input, context_input], verbose=0)
            predicted_class = int(np.argmax(predictions[0]))
            confidence = float(predictions[0][predicted_class])
            return predicted_class, confidence
        else:
            return self._synthetic_predict(sequence, context)

    def _synthetic_predict(self, sequence: np.ndarray, context: np.ndarray) -> tuple:
        avg_anger = np.mean(sequence[:, 3])
        avg_contempt = np.mean(sequence[:, 4])
        avg_disgust = np.mean(sequence[:, 5])
        avg_sadness = np.mean(sequence[:, 7])
        
        avg_looking = np.mean(sequence[:, 8])
        avg_sleeping = np.mean(sequence[:, 11])
        avg_eye_openness = np.mean(sequence[:, 12])
        avg_face_detected = np.mean(sequence[:, 13])
        
        frustration_score = (avg_anger + avg_contempt + avg_disgust + avg_sadness) / 4.0
        attention_score = (avg_looking + avg_face_detected + (1.0 - avg_sleeping)) / 3.0
        drowsiness_score = avg_sleeping + (1.0 - avg_eye_openness)
        
        prev_vibrations = context[3]
        prev_instructions = context[4]
        
        if frustration_score > 0.4 and prev_instructions >= 1:
            return 3, min(0.7 + frustration_score * 0.2, 0.95)
        
        if (attention_score < 0.5 or drowsiness_score > 0.6) and prev_vibrations >= 2:
            return 3, min(0.65 + (1.0 - attention_score) * 0.2, 0.95)
        
        if frustration_score > 0.35:
            return 2, min(0.6 + frustration_score * 0.3, 0.95)
        
        if attention_score < 0.6 or drowsiness_score > 0.5:
            return 1, min(0.6 + (1.0 - attention_score) * 0.3, 0.95)
        
        return 0, 0.8

    def unload(self) -> None:
        self._model = None
        self._is_loaded = False