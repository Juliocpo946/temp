from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session as DBSession
from src.application.dtos.biometric_frame_dto import BiometricFrameDTO
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO
from src.domain.entities.intervention import Intervention
from src.domain.entities.cognitive_state_entity import CognitiveStateEntity
from src.domain.entities.detection_decision import DetectionDecision
from src.domain.value_objects.cognitive_state import CognitiveState
from src.domain.value_objects.intervention_type import InterventionType
from src.domain.services.intervention_controller import InterventionController, SessionContext
from src.domain.services.intervention_policy import InterventionPolicy
from src.infrastructure.ml.temporal_feature_extractor import TemporalFeatureExtractor
from src.infrastructure.ml.cognitive_state_detector import CognitiveStateDetector
from src.infrastructure.ml.feature_buffer import FeatureBuffer
from src.infrastructure.ml.pattern_analyzer import PatternAnalyzer
from src.infrastructure.messaging.monitoring_publisher import MonitoringPublisher
from src.infrastructure.persistence.repositories.intervention_repository import InterventionRepository
from src.infrastructure.persistence.repositories.cognitive_state_repository import CognitiveStateRepository
from src.infrastructure.persistence.repositories.detection_decision_repository import DetectionDecisionRepository


class ProcessBiometricFrameUseCase:
    def __init__(
        self,
        db: DBSession,
        feature_buffer: FeatureBuffer,
        feature_extractor: TemporalFeatureExtractor,
        state_detector: CognitiveStateDetector,
        context: SessionContext,
        activity_uuid: str,
        session_id: str,
        user_id: int,
        external_activity_id: int,
        correlation_id: Optional[str] = None
    ):
        self.db = db
        self.feature_buffer = feature_buffer
        self.feature_extractor = feature_extractor
        self.state_detector = state_detector
        self.context = context
        self.activity_uuid = activity_uuid
        self.session_id = session_id
        self.user_id = user_id
        self.external_activity_id = external_activity_id
        self.correlation_id = correlation_id or str(uuid.uuid4())

        self.policy = InterventionPolicy()
        self.controller = InterventionController()
        self.pattern_analyzer = PatternAnalyzer()
        self.publisher = MonitoringPublisher()
        
        self.intervention_repo = InterventionRepository(db)
        self.cognitive_state_repo = CognitiveStateRepository(db)
        self.decision_repo = DetectionDecisionRepository(db)
        
        self.current_state_entity: Optional[CognitiveStateEntity] = None

    def execute(self, frame: BiometricFrameDTO) -> Optional[Dict[str, Any]]:
        if self._activity_changed(self.external_activity_id):
            self._reset_for_new_activity()

        features = self.feature_extractor.extract(frame)
        self.feature_buffer.add(features, frame.to_dict())

        if not self.feature_buffer.is_ready():
            return None

        detected_state, confidence, cluster_id = self.state_detector.detect_state(features)

        if detected_state == CognitiveState.INITIALIZING:
            return None

        state_changed = self._handle_state_change(
            detected_state,
            confidence,
            cluster_id,
            features
        )

        if not state_changed and not detected_state.requires_intervention():
            return None

        trajectory = self.state_detector.get_state_trajectory(window_size=10)
        stability = self.state_detector.get_stability_score(window_size=10)
        
        state_duration = self._calculate_state_duration()
        
        pattern_analysis = self.pattern_analyzer.analyze_trajectory(trajectory)
        decision_score = pattern_analysis.get("severity", 0.0) * confidence

        should_intervene, intervention_type, reason, final_score = self.policy.evaluate(
            current_state=detected_state,
            state_duration=state_duration,
            trajectory=trajectory,
            decision_score=decision_score,
            intervention_counts=self.context.get_intervention_counts(),
            effectiveness_history=self.context.get_effectiveness_history()
        )

        decision = self._create_detection_decision(
            should_intervene,
            intervention_type,
            reason,
            final_score,
            pattern_analysis
        )

        if not should_intervene:
            return None

        if not self.controller.can_intervene(intervention_type, self.context):
            print(f"[PROCESS_FRAME] [INFO] Cooldown activo para {intervention_type.to_string()}")
            return None

        intervention = self._create_intervention(
            decision,
            intervention_type,
            trajectory
        )

        self._publish_event(intervention, decision_score)
        self.context.record_intervention(intervention_type)

        return {
            "type": "intervention",
            "intervention_id": str(intervention.id),
            "intervention_type": intervention_type.to_string(),
            "cognitive_state": detected_state.to_string(),
            "confidence": final_score,
            "correlation_id": self.correlation_id
        }

    def _activity_changed(self, external_activity_id: int) -> bool:
        if self.context.current_external_activity_id is None:
            return True
        return self.context.current_external_activity_id != external_activity_id

    def _reset_for_new_activity(self) -> None:
        self.feature_buffer.clear()
        self.feature_extractor.reset()
        self.state_detector.reset()
        self.context.reset_for_activity(self.external_activity_id)
        self.current_state_entity = None
        print(f"[PROCESS_FRAME] [INFO] Contexto reiniciado para actividad: {self.external_activity_id}")

    def _handle_state_change(
        self,
        new_state: CognitiveState,
        confidence: float,
        cluster_id: int,
        features
    ) -> bool:
        previous_state = self.state_detector.get_current_state()
        
        if previous_state == new_state and self.current_state_entity:
            return False

        if self.current_state_entity:
            self.current_state_entity.end_state()
            self.cognitive_state_repo.update(self.current_state_entity)

        stability = self.state_detector.get_stability_score()

        new_state_entity = CognitiveStateEntity(
            id=None,
            user_id=self.user_id,
            session_id=uuid.UUID(self.session_id),
            activity_uuid=uuid.UUID(self.activity_uuid),
            state_type=new_state.to_string(),
            cluster_id=cluster_id,
            confidence_score=confidence,
            stability_score=stability,
            started_at=datetime.utcnow(),
            ended_at=None,
            duration_seconds=None,
            features_snapshot={"features": features.tolist()[:20]},
            previous_state_id=self.current_state_entity.id if self.current_state_entity else None
        )

        self.current_state_entity = self.cognitive_state_repo.create(new_state_entity)
        
        print(f"[PROCESS_FRAME] [INFO] Cambio de estado: {previous_state} -> {new_state}, confidence={confidence:.2f}")
        
        return True

    def _calculate_state_duration(self) -> int:
        if not self.current_state_entity or not self.current_state_entity.started_at:
            return 0
        
        now = datetime.utcnow()
        delta = now - self.current_state_entity.started_at
        return int(delta.total_seconds())

    def _create_detection_decision(
        self,
        should_intervene: bool,
        intervention_type: Optional[InterventionType],
        reason,
        score: float,
        pattern_analysis: Dict
    ) -> DetectionDecision:
        cooldown_active = False
        cooldown_until = None
        
        if should_intervene and intervention_type:
            cooldown_active = self.controller.is_cooldown_active(intervention_type, self.context)

        context_data = {
            "pattern_analysis": pattern_analysis,
            "intervention_counts": self.context.get_intervention_counts(),
            "effectiveness_history": self.context.get_effectiveness_history(),
            "correlation_id": self.correlation_id
        }

        decision = DetectionDecision(
            id=None,
            cognitive_state_id=self.current_state_entity.id if self.current_state_entity else uuid.uuid4(),
            should_intervene=should_intervene,
            intervention_type=intervention_type.to_string() if intervention_type else None,
            decision_score=score,
            reason_code=reason.to_string(),
            cooldown_active=cooldown_active,
            cooldown_until=cooldown_until,
            context_data=context_data,
            decided_at=datetime.utcnow()
        )

        return self.decision_repo.create(decision)

    def _create_intervention(
        self,
        decision: DetectionDecision,
        intervention_type: InterventionType,
        trajectory: list
    ) -> Intervention:
        pre_snapshot = {
            "trajectory": [s.to_string() for s in trajectory],
            "state_duration": self._calculate_state_duration(),
            "recent_frames": self.feature_buffer.get_raw_frames(10)
        }

        intervention = Intervention(
            id=None,
            detection_decision_id=decision.id,
            user_id=self.user_id,
            session_id=uuid.UUID(self.session_id),
            activity_uuid=uuid.UUID(self.activity_uuid),
            external_activity_id=self.external_activity_id,
            intervention_type=intervention_type.to_string(),
            triggered_at=datetime.utcnow(),
            pre_state_snapshot=pre_snapshot,
            post_state_snapshot=None,
            effectiveness_score=None,
            evaluated_at=None,
            evaluation_method=None
        )

        return self.intervention_repo.create(intervention)

    def _publish_event(self, intervention: Intervention, decision_score: float) -> None:
        context_data = {
            "intentos_previos": self.context.instruction_count,
            "tiempo_en_estado": self._calculate_state_duration(),
            "correlation_id": self.correlation_id,
            "precision_cognitiva": decision_score,
            "activity_uuid": self.activity_uuid
        }

        event = MonitoringEventDTO(
            session_id=self.session_id,
            user_id=self.user_id,
            external_activity_id=self.external_activity_id,
            activity_uuid=self.activity_uuid,
            intervention_type=intervention.intervention_type,
            confidence=decision_score,
            context=context_data,
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )

        self.publisher.publish(event, self.correlation_id)