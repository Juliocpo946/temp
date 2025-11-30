from typing import Dict, Any, List

class BiometricFrameDTO:
    def __init__(
        self,
        timestamp: str,
        emocion_principal: Dict[str, Any],
        desglose_emociones: List[Dict[str, Any]],
        atencion: Dict[str, Any],
        somnolencia: Dict[str, Any],
        rostro_detectado: bool
    ):
        self.timestamp = timestamp
        self.emocion_principal = emocion_principal
        self.desglose_emociones = desglose_emociones
        self.atencion = atencion
        self.somnolencia = somnolencia
        self.rostro_detectado = rostro_detectado

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BiometricFrameDTO':
        metadata = data.get("metadata", {})
        analisis = data.get("analisis_sentimiento", {})
        biometricos = data.get("datos_biometricos", {})
        
        return cls(
            timestamp=metadata.get("timestamp"),
            emocion_principal=analisis.get("emocion_principal", {}),
            desglose_emociones=analisis.get("desglose_emociones", []),
            atencion=biometricos.get("atencion", {}),
            somnolencia=biometricos.get("somnolencia", {}),
            rostro_detectado=biometricos.get("rostro_detectado", False)
        )

    def get_emotion_value(self, emotion_name: str) -> float:
        for emotion in self.desglose_emociones:
            if emotion.get("emocion", "").lower() == emotion_name.lower():
                return emotion.get("confianza", 0.0) / 100.0
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "emocion_principal": self.emocion_principal,
            "desglose_emociones": self.desglose_emociones,
            "atencion": self.atencion,
            "somnolencia": self.somnolencia,
            "rostro_detectado": self.rostro_detectado
        }