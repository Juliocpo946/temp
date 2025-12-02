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
        context: SessionContext,
        activity_uuid: str,
        session_id: str,
        user_id: int,
        external_activity_id: int,
        correlation_id: Optional[str] = None
    ):
        self.db = db
        self.buffer = buffer
        self.context = context
        self.activity_uuid = activity_uuid
        self.session_id = session_id
        self.user_id = user_id
        self.external_activity_id = external_activity_id
        self.correlation_id = correlation_id or str(uuid.uuid4())

        self.feature_extractor = FeatureExtractor()
        self.classifier = InterventionClassifier()
        self.controller = InterventionController()
        self.publisher = MonitoringPublisher()
        self.intervention_repo = InterventionRepository(db)
        self.training_sample_repo = TrainingSampleRepository(db)

    def execute(self, frame: BiometricFrameDTO) -> Optional[Dict[str, Any]]:
        if self._activity_changed(self.external_activity_id):
            self._reset_for_new_activity()

        features = self.feature_extractor.extract(frame)
        self.buffer.add(features, frame.to_dict())

        if not self.buffer.is_ready():
            return None

        sequence = self.buffer.get_sequence()
        context_vector = self.context.get_context_vector()

        intervention_type, confidence = self.classifier.predict(sequence, context_vector)

        if intervention_type == InterventionType.NO_INTERVENTION:
            self._maybe_store_negative_sample(sequence, context_vector)
            return None

        if self.controller.is_cooldown_active(intervention_type, self.context):
            return None

        intervention = self._create_intervention(intervention_type, confidence, frame)
        self._store_training_sample(sequence, context_vector, intervention)
        self._publish_event(intervention, frame)
        self.context.record_intervention(intervention_type)

        return {
            "type": "intervention",
            "intervention_id": str(intervention.id),
            "intervention_type": intervention_type.value,
            "confidence": confidence,
            "correlation_id": self.correlation_id
        }

    def _activity_changed(self, external_activity_id: int) -> bool:
        if self.context.current_external_activity_id is None:
            return True
        return self.context.current_external_activity_id != external_activity_id

    def _reset_for_new_activity(self) -> None:
        self.buffer.clear()
        self.context.reset_for_activity(self.external_activity_id)
        print(f"[INFO] Contexto reiniciado para nueva actividad: {self.external_activity_id}")

    def _create_intervention(
        self,
        intervention_type: InterventionType,
        confidence: float,
        frame: BiometricFrameDTO
    ) -> Intervention:
        cognitive_event = self._map_intervention_to_cognitive_event(intervention_type)

        precision = 0.0
        if frame.emocion_principal:
            precision = frame.emocion_principal.get("confianza", 0.0)

        intervention = Intervention(
            id=None,
            activity_uuid=uuid.UUID(self.activity_uuid),
            session_id=uuid.UUID(self.session_id),
            user_id=self.user_id,
            external_activity_id=self.external_activity_id,
            intervention_type=intervention_type.to_string(),
            cognitive_event=cognitive_event,
            confidence=confidence,
            precision=precision,
            triggered_at=datetime.utcnow(),
            result=None,
            evaluated_at=None
        )

        return self.intervention_repo.create(intervention)

    def _map_intervention_to_cognitive_event(self, intervention_type: InterventionType) -> str:
        mapping = {
            InterventionType.VIBRATION: "desatencion",
            InterventionType.INSTRUCTION: "frustracion",
            InterventionType.PAUSE: "cansancio_cognitivo"
        }
        return mapping.get(intervention_type, "desconocido")

    def _store_training_sample(
        self,
        sequence,
        context_vector,
        intervention: Intervention
    ) -> None:
        sample = TrainingSample(
            id=None,
            intervention_id=intervention.id,
            external_activity_id=self.external_activity_id,
            window_data=sequence.tolist(),
            context_data=context_vector.tolist(),
            label=str(intervention.intervention_type),
            source="realtime",
            created_at=datetime.utcnow()
        )
        self.training_sample_repo.create(sample)

    def _maybe_store_negative_sample(self, sequence, context_vector) -> None:
        if random.random() < NEGATIVE_SAMPLE_RATE:
            sample = TrainingSample(
                id=None,
                intervention_id=None,
                external_activity_id=self.external_activity_id,
                window_data=sequence.tolist(),
                context_data=context_vector.tolist(),
                label="no_intervention",
                source="realtime",
                created_at=datetime.utcnow()
            )
            self.training_sample_repo.create(sample)

    def _publish_event(self, intervention: Intervention, frame: BiometricFrameDTO) -> None:
        context_data = {
            "intentos_previos": self.context.instruction_count,
            "tiempo_en_estado": 0,
            "correlation_id": self.correlation_id,
            "precision_cognitiva": intervention.precision
        }

        event = MonitoringEventDTO(
            session_id=self.session_id,
            user_id=self.user_id,
            external_activity_id=self.external_activity_id,
            activity_uuid=self.activity_uuid,
            intervention_type=intervention.intervention_type,
            confidence=intervention.confidence,
            context=context_data,
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        self.publisher.publish(event, self.correlation_id)