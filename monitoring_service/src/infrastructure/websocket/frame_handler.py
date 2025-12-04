import json
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session as DBSession
from src.infrastructure.websocket.connection_manager import ConnectionState
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.process_biometric_frame import ProcessBiometricFrameUseCase
from src.application.use_cases.evaluate_intervention import EvaluateInterventionUseCase
from src.application.dtos.biometric_frame_dto import BiometricFrameDTO
from src.infrastructure.ml.temporal_feature_extractor import TemporalFeatureExtractor
from src.infrastructure.ml.cognitive_state_detector import CognitiveStateDetector


class FrameHandler:
    def __init__(self, db: DBSession, rabbitmq_client: Optional[RabbitMQClient] = None):
        self.db = db
        self.rabbitmq_client = rabbitmq_client or RabbitMQClient()

    async def handle(self, state: ConnectionState, raw_message: str) -> Optional[Dict[str, Any]]:
        correlation_id = str(uuid.uuid4())
        
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            return {
                "error": "JSON invalido",
                "code": "INVALID_JSON",
                "correlation_id": correlation_id
            }

        message_type = data.get("type", "frame")

        if message_type == "handshake":
            return self._handle_handshake(state, data, correlation_id)
        elif message_type == "frame" or "metadata" in data:
            if not state.is_ready:
                return {
                    "error": "Handshake requerido antes de enviar frames",
                    "code": "HANDSHAKE_REQUIRED",
                    "correlation_id": correlation_id
                }
            return await self._handle_frame_with_backpressure(state, data, correlation_id)
        elif message_type == "ping":
            return {
                "type": "pong", 
                "timestamp": data.get("timestamp"),
                "correlation_id": correlation_id
            }
        elif message_type == "get_metrics":
            return self._handle_get_metrics(state, correlation_id)
        else:
            return {
                "error": f"Tipo de mensaje no reconocido: {message_type}",
                "code": "UNKNOWN_MESSAGE_TYPE",
                "correlation_id": correlation_id
            }

    def _handle_handshake(self, state: ConnectionState, data: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        user_id = data.get("user_id")
        external_activity_id = data.get("external_activity_id")
        company_id = data.get("company_id")

        if not user_id or not external_activity_id:
            return {
                "error": "user_id y external_activity_id son requeridos",
                "code": "MISSING_REQUIRED_FIELDS",
                "correlation_id": correlation_id
            }

        try:
            user_id = int(user_id)
            external_activity_id = int(external_activity_id)
        except (ValueError, TypeError):
            return {
                "error": "user_id y external_activity_id deben ser enteros",
                "code": "INVALID_FIELD_TYPE",
                "correlation_id": correlation_id
            }

        state.set_metadata(user_id, external_activity_id, company_id)

        print(f"[FRAME_HANDLER] [INFO] Handshake completado para actividad {state.activity_uuid}: user={user_id}, ext_activity={external_activity_id}")

        return {
            "type": "handshake_ack",
            "status": "ready",
            "activity_uuid": state.activity_uuid,
            "session_id": state.session_id,
            "correlation_id": correlation_id,
            "backpressure_config": {
                "max_buffer_size": state.MAX_BUFFER_SIZE,
                "max_frames_per_second": state.MAX_FRAMES_PER_SECOND,
                "throttle_threshold": state.THROTTLE_THRESHOLD
            }
        }

    async def _handle_frame_with_backpressure(self, state: ConnectionState, data: Dict[str, Any], correlation_id: str) -> Optional[Dict[str, Any]]:
        if not state.can_accept_frame():
            if state._backpressure.is_throttled:
                throttle_msg = state.get_throttle_message()
                throttle_msg["correlation_id"] = correlation_id
                return throttle_msg
            
            return {
                "type": "frame_dropped",
                "reason": "buffer_full",
                "correlation_id": correlation_id,
                "buffer_size": state.get_buffer_size(),
                "max_buffer_size": state.MAX_BUFFER_SIZE
            }

        state.add_frame_to_buffer(data)

        return await self._process_frame(state, data, correlation_id)

    async def _process_frame(self, state: ConnectionState, data: Dict[str, Any], correlation_id: str) -> Optional[Dict[str, Any]]:
        frame = BiometricFrameDTO.from_dict(data)

        use_case = ProcessBiometricFrameUseCase(
            db=self.db,
            feature_buffer=state.feature_buffer,
            feature_extractor=state.feature_extractor,
            state_detector=state.state_detector,
            context=state.context,
            activity_uuid=state.activity_uuid,
            session_id=state.session_id,
            user_id=state.metadata.user_id,
            external_activity_id=state.metadata.external_activity_id,
            correlation_id=correlation_id
        )
        result = use_case.execute(frame)

        evaluator = EvaluateInterventionUseCase(self.db, self.rabbitmq_client)
        evaluator.execute(state.feature_buffer, state.session_id, state.activity_uuid)

        if result:
            result["correlation_id"] = correlation_id

        return result

    def _handle_get_metrics(self, state: ConnectionState, correlation_id: str) -> Dict[str, Any]:
        metrics = state.get_backpressure_metrics()
        metrics["type"] = "metrics_response"
        metrics["correlation_id"] = correlation_id
        return metrics