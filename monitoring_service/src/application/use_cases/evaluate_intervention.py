from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session as DBSession
from src.domain.entities.intervention import Intervention
from src.domain.services.effectiveness_tracker import EffectivenessTracker
from src.domain.value_objects.cognitive_state import CognitiveState
from src.infrastructure.persistence.repositories.intervention_repository import InterventionRepository
from src.infrastructure.persistence.repositories.cognitive_state_repository import CognitiveStateRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.intervention_evaluation_publisher import InterventionEvaluationPublisher
from src.infrastructure.ml.feature_buffer import FeatureBuffer
from src.infrastructure.config.settings import INTERVENTION_EVALUATION_DELAY


class EvaluateInterventionUseCase:
    def __init__(
        self,
        db: DBSession,
        rabbitmq_client: Optional[RabbitMQClient] = None
    ):
        self.db = db
        self.intervention_repo = InterventionRepository(db)
        self.state_repo = CognitiveStateRepository(db)
        self.effectiveness_tracker = EffectivenessTracker()
        self.evaluation_publisher = None
        
        if rabbitmq_client:
            self.evaluation_publisher = InterventionEvaluationPublisher(rabbitmq_client)

    def execute(
        self,
        feature_buffer: FeatureBuffer,
        session_id: str,
        activity_uuid: str
    ) -> List[str]:
        threshold_time = datetime.utcnow() - timedelta(seconds=INTERVENTION_EVALUATION_DELAY)
        pending_interventions = self.intervention_repo.get_pending_evaluations(threshold_time)

        evaluated_ids = []
        for intervention in pending_interventions:
            success = self._evaluate_single(intervention, feature_buffer)
            if success:
                evaluated_ids.append(str(intervention.id))
                
                if self.evaluation_publisher:
                    self._publish_evaluation(intervention, session_id, activity_uuid)

        return evaluated_ids

    def _evaluate_single(
        self,
        intervention: Intervention,
        feature_buffer: FeatureBuffer
    ) -> bool:
        if not feature_buffer.is_ready():
            return False

        pre_snapshot = intervention.pre_state_snapshot
        pre_trajectory = pre_snapshot.get("trajectory", [])
        
        if not pre_trajectory:
            return False

        pre_state = CognitiveState.from_string(pre_trajectory[-1])
        
        recent_states = self.state_repo.get_recent_by_session(
            str(intervention.session_id),
            limit=5
        )
        
        if not recent_states:
            return False

        post_state = CognitiveState.from_string(recent_states[0].state_type)
        
        pre_features_data = pre_snapshot.get("recent_frames", [])
        if pre_features_data and len(pre_features_data) > 0:
            last_pre_frame = pre_features_data[-1]
            pre_features = self._extract_features_from_frame(last_pre_frame)
        else:
            pre_features = np.zeros(13, dtype=np.float32)

        post_features_list = feature_buffer.get_recent_features(10)
        if post_features_list is not None and len(post_features_list) > 0:
            post_features = post_features_list[-1][:13]
        else:
            post_features = np.zeros(13, dtype=np.float32)

        effectiveness_score = self.effectiveness_tracker.calculate_effectiveness(
            intervention_type=intervention.intervention_type,
            pre_state=pre_state,
            post_state=post_state,
            pre_features=pre_features,
            post_features=post_features
        )

        post_snapshot = {
            "post_state": post_state.to_string(),
            "recent_states": [s.state_type for s in recent_states[:3]],
            "evaluation_time": datetime.utcnow().isoformat()
        }

        intervention.evaluate(
            effectiveness_score=effectiveness_score,
            post_state_snapshot=post_snapshot,
            evaluation_method="state_and_feature_comparison"
        )

        self.intervention_repo.update(intervention)
        
        print(f"[EVALUATE_INTERVENTION] [INFO] Intervencion {intervention.id} evaluada: score={effectiveness_score:.2f}")
        
        return True

    def _extract_features_from_frame(self, frame_dict: Dict) -> np.ndarray:
        features = np.zeros(13, dtype=np.float32)
        
        desglose = frame_dict.get("desglose_emociones", [])
        emotion_map = {e.get("emocion", "").lower(): e.get("confianza", 0.0) / 100.0 for e in desglose}
        
        features[0] = emotion_map.get("happiness", 0.0)
        features[1] = emotion_map.get("neutral", 0.0)
        features[2] = emotion_map.get("surprise", 0.0)
        features[3] = emotion_map.get("anger", 0.0)
        features[4] = emotion_map.get("contempt", 0.0)
        features[5] = emotion_map.get("disgust", 0.0)
        features[6] = emotion_map.get("fear", 0.0)
        features[7] = emotion_map.get("sadness", 0.0)
        
        atencion = frame_dict.get("atencion", {})
        features[8] = 1.0 if atencion.get("mirando_pantalla", False) else 0.0
        
        orientacion = atencion.get("orientacion_cabeza", {})
        features[9] = np.clip(orientacion.get("pitch", 0.0) / 45.0, -1.0, 1.0)
        features[10] = np.clip(orientacion.get("yaw", 0.0) / 45.0, -1.0, 1.0)
        
        somnolencia = frame_dict.get("somnolencia", {})
        features[11] = 1.0 if somnolencia.get("esta_durmiendo", False) else 0.0
        features[12] = somnolencia.get("apertura_ojos_ear", 0.3)
        
        return features

    def _publish_evaluation(
        self,
        intervention: Intervention,
        session_id: str,
        activity_uuid: str
    ) -> None:
        if not self.evaluation_publisher:
            return

        result_str = "positive" if intervention.effectiveness_score >= 0.6 else \
                     "negative" if intervention.effectiveness_score < 0.4 else "sin_efecto"

        self.evaluation_publisher.publish_evaluation(
            intervention_id=str(intervention.id),
            session_id=session_id,
            activity_uuid=activity_uuid,
            cognitive_event=self._map_intervention_to_event(intervention.intervention_type),
            intervention_type=intervention.intervention_type,
            result=result_str,
            topic=None,
            content_type=intervention.intervention_type,
            precision_before=None,
            precision_after=intervention.effectiveness_score
        )

    def _map_intervention_to_event(self, intervention_type: str) -> str:
        mapping = {
            "vibration": "desatencion",
            "instruction": "frustracion",
            "pause": "cansancio_cognitivo"
        }
        return mapping.get(intervention_type, "desconocido")