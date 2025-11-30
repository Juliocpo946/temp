from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import random
from sqlalchemy.orm import Session as DBSession
from src.application.dtos.biometric_frame_dto import BiometricFrameDTO
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO
from src.domain.entities.intervention import Intervention
from src.domain.entities.training_sample import TrainingSample
from src.domain.value_objects.intervention_type import InterventionType
from src.domain.services.intervention_controller import InterventionController, SessionContext
from src.infrastructure.ml.feature_extractor import FeatureExtractor
from src.infrastructure.ml.sequence_buffer import SequenceBuffer
from src.infrastructure.ml.intervention_classifier import InterventionClassifier
from src.infrastructure.messaging.monitoring_publisher import MonitoringPublisher
from src.infrastructure.persistence.repositories.intervention_repository import InterventionRepository
from src.infrastructure.persistence.repositories.training_sample_repository import TrainingSampleRepository
from src.infrastructure.config.settings import NEGATIVE_SAMPLE_RATE

class ProcessBiometricFrameUseCase:
    def __init__(
        self,
        db: DBSession,
        buffer: SequenceBuffer,
        context: SessionContext
    ):
        self.db = db
        self.buffer = buffer
        self.context = context
        self.feature_extractor = FeatureExtractor()
        self.classifier = InterventionClassifier()
        self.controller = InterventionController()
        self.publisher = MonitoringPublisher()
        self.intervention_repo = InterventionRepository(db)
        self.training_sample_repo = TrainingSampleRepository(db)

    def execute(self, frame: BiometricFrameDTO) -> Optional[Dict[str, Any]]:
        if self._activity_changed(frame.external_activity_id):
            self.buffer.clear()
            self.context.reset_for_activity(frame.external_activity_id)

        features = self.feature_extractor.extract(frame)
        raw_frame = self._frame_to_dict(frame)
        self.buffer.add(features, raw_frame)

        if not self.buffer.is_ready():
            return None

        sequence = self.buffer.get_sequence()
        context_vector = self.context.get_context_vector()

        intervention_type, confidence = self.classifier.classify(sequence, context_vector)

        if not self.classifier.should_intervene(intervention_type, confidence):
            self._maybe_save_negative_sample(frame, sequence, context_vector)
            return None

        if not self.controller.can_intervene(intervention_type, self.context):
            return None

        intervention = self._create_intervention(
            frame, intervention_type, confidence, sequence, context_vector
        )

        self.context.register_intervention(intervention_type)

        event = MonitoringEventDTO(
            session_id=frame.session_id,
            user_id=frame.user_id,
            external_activity_id=frame.external_activity_id,
            intervention_type=intervention_type.to_string(),
            confidence=confidence,
            context={
                "precision_cognitiva": frame.emocion_principal.get("confianza", 0.5),
                "intentos_previos": self._get_previous_attempts(intervention_type),
                "tiempo_en_estado": self._estimate_time_in_state()
            },
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        self.publisher.publish_intervention(event)

        return {
            "intervention_id": str(intervention.id),
            "type": intervention_type.to_string(),
            "confidence": confidence
        }

    def _activity_changed(self, external_activity_id: int) -> bool:
        if self.context.current_external_activity_id is None:
            return True
        return self.context.current_external_activity_id != external_activity_id

    def _frame_to_dict(self, frame: BiometricFrameDTO) -> Dict[str, Any]:
        return {
            "timestamp": frame.timestamp,
            "emocion_principal": frame.emocion_principal,
            "desglose_emociones": frame.desglose_emociones,
            "atencion": frame.atencion,
            "somnolencia": frame.somnolencia,
            "rostro_detectado": frame.rostro_detectado
        }

    def _create_intervention(
        self,
        frame: BiometricFrameDTO,
        intervention_type: InterventionType,
        confidence: float,
        sequence,
        context_vector
    ) -> Intervention:
        intervention = Intervention(
            id=None,
            session_id=uuid.UUID(frame.session_id),
            external_activity_id=frame.external_activity_id,
            intervention_type=intervention_type.to_string(),
            confidence=confidence,
            triggered_at=datetime.utcnow(),
            window_snapshot={"frames": self.buffer.get_snapshot()},
            context_snapshot=self.context.get_snapshot()
        )

        saved_intervention = self.intervention_repo.create(intervention)

        training_sample = TrainingSample(
            id=None,
            intervention_id=saved_intervention.id,
            external_activity_id=frame.external_activity_id,
            window_data={"sequence": sequence.tolist()},
            context_data={"context": context_vector.tolist()},
            label=intervention_type.value,
            source="production"
        )
        self.training_sample_repo.create(training_sample)

        return saved_intervention

    def _maybe_save_negative_sample(
        self,
        frame: BiometricFrameDTO,
        sequence,
        context_vector
    ) -> None:
        if random.random() < NEGATIVE_SAMPLE_RATE:
            training_sample = TrainingSample(
                id=None,
                intervention_id=None,
                external_activity_id=frame.external_activity_id,
                window_data={"sequence": sequence.tolist()},
                context_data={"context": context_vector.tolist()},
                label=0,
                source="production"
            )
            self.training_sample_repo.create(training_sample)

    def _get_previous_attempts(self, intervention_type: InterventionType) -> int:
        if intervention_type == InterventionType.VIBRATION:
            return self.context.vibration_count
        elif intervention_type == InterventionType.INSTRUCTION:
            return self.context.instruction_count
        elif intervention_type == InterventionType.PAUSE:
            return self.context.pause_count
        return 0

    def _estimate_time_in_state(self) -> int:
        return len(self.buffer)