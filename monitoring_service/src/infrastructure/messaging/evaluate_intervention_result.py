from typing import List, Optional
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session as DBSession
from src.domain.entities.intervention import Intervention
from src.domain.value_objects.intervention_result import InterventionResult
from src.infrastructure.persistence.repositories.intervention_repository import InterventionRepository
from src.infrastructure.persistence.repositories.training_sample_repository import TrainingSampleRepository
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.intervention_evaluation_publisher import InterventionEvaluationPublisher
from src.infrastructure.ml.sequence_buffer import SequenceBuffer
from src.infrastructure.config.settings import RESULT_EVALUATION_DELAY_SECONDS


class EvaluateInterventionResultUseCase:
    NEGATIVE_EMOTION_INDICES = [3, 4, 5, 6, 7]
    ATTENTION_INDEX = 8
    FACE_DETECTED_INDEX = 13

    def __init__(self, db: DBSession, rabbitmq_client: Optional[RabbitMQClient] = None):
        self.db = db
        self.intervention_repo = InterventionRepository(db)
        self.training_sample_repo = TrainingSampleRepository(db)
        self.rabbitmq_client = rabbitmq_client
        self.evaluation_publisher = None
        if rabbitmq_client:
            self.evaluation_publisher = InterventionEvaluationPublisher(rabbitmq_client)

    def execute(self, buffer: SequenceBuffer, session_id: str = None, activity_uuid: str = None) -> List[str]:
        threshold_time = datetime.utcnow() - timedelta(seconds=RESULT_EVALUATION_DELAY_SECONDS)
        pending_interventions = self.intervention_repo.get_pending_evaluations(threshold_time)

        evaluated_ids = []
        for intervention in pending_interventions:
            result = self._evaluate_single(intervention, buffer)
            if result:
                intervention.evaluate_result(result.value)
                self.intervention_repo.update(intervention)
                self._update_training_sample_label(intervention, result)
                
                if self.evaluation_publisher:
                    self._publish_evaluation(intervention, result, session_id, activity_uuid)
                
                evaluated_ids.append(str(intervention.id))

        return evaluated_ids

    def _evaluate_single(
        self,
        intervention: Intervention,
        buffer: SequenceBuffer
    ) -> Optional[InterventionResult]:
        if not buffer.is_ready():
            return None

        recent_frames = buffer.get_recent_frames(15)
        if len(recent_frames) < 10:
            return None

        recent_array = np.array(recent_frames)

        avg_negative = np.mean(recent_array[:, self.NEGATIVE_EMOTION_INDICES])
        avg_attention = np.mean(recent_array[:, self.ATTENTION_INDEX])
        avg_face_detected = np.mean(recent_array[:, self.FACE_DETECTED_INDEX])

        intervention_type = intervention.intervention_type

        if intervention_type == "vibration":
            if avg_attention > 0.7 and avg_face_detected > 0.8:
                return InterventionResult.POSITIVE
            elif avg_attention < 0.4:
                return InterventionResult.NEGATIVE
            else:
                return InterventionResult.NO_EFFECT

        elif intervention_type == "instruction":
            if avg_negative < 0.3 and avg_attention > 0.6:
                return InterventionResult.POSITIVE
            elif avg_negative > 0.5:
                return InterventionResult.NEGATIVE
            else:
                return InterventionResult.NO_EFFECT

        elif intervention_type == "pause":
            if avg_negative < 0.2 and avg_attention > 0.7:
                return InterventionResult.POSITIVE
            else:
                return InterventionResult.NO_EFFECT

        return InterventionResult.NO_EFFECT

    def _update_training_sample_label(
        self,
        intervention: Intervention,
        result: InterventionResult
    ) -> None:
        sample = self.training_sample_repo.get_by_intervention_id(intervention.id)
        if sample:
            if result == InterventionResult.POSITIVE:
                sample.label = intervention.intervention_type
            elif result == InterventionResult.NEGATIVE:
                sample.label = "no_intervention"
            self.training_sample_repo.update(sample)

    def _publish_evaluation(
        self,
        intervention: Intervention,
        result: InterventionResult,
        session_id: str,
        activity_uuid: str
    ) -> None:
        if not self.evaluation_publisher:
            return

        result_str = "positive" if result == InterventionResult.POSITIVE else \
                     "negative" if result == InterventionResult.NEGATIVE else "sin_efecto"

        self.evaluation_publisher.publish_evaluation(
            intervention_id=str(intervention.id),
            session_id=session_id or str(intervention.session_id),
            activity_uuid=activity_uuid or str(intervention.activity_uuid),
            cognitive_event=intervention.cognitive_event,
            intervention_type=intervention.intervention_type,
            result=result_str,
            topic=getattr(intervention, 'topic', None),
            content_type=intervention.intervention_type,
            precision_before=intervention.precision,
            precision_after=None
        )