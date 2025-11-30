from typing import Optional, Dict, Any
import json
from sqlalchemy.orm import Session as DBSession
from src.application.dtos.biometric_frame_dto import BiometricFrameDTO
from src.application.use_cases.process_biometric_frame import ProcessBiometricFrameUseCase
from src.application.use_cases.evaluate_intervention_result import EvaluateInterventionResultUseCase
from src.infrastructure.websocket.connection_manager import ConnectionState
from src.infrastructure.messaging.activity_event_consumer import ActivityStateManager

class FrameHandler:
    def __init__(self, db: DBSession):
        self.db = db
        self.state_manager = ActivityStateManager()

    async def handle(self, state: ConnectionState, raw_message: str) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(raw_message)
            
            if not state.is_ready:
                return self._handle_handshake(state, data)
            
            if self.state_manager.is_paused(state.activity_uuid):
                return None
            
            return await self._handle_frame(state, data)

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON invalido: {e}")
            return {"error": "JSON invalido", "code": "INVALID_JSON"}
        except Exception as e:
            print(f"[ERROR] Error procesando mensaje: {e}")
            return {"error": str(e), "code": "PROCESSING_ERROR"}

    def _handle_handshake(self, state: ConnectionState, data: Dict[str, Any]) -> Dict[str, Any]:
        msg_type = data.get("type")
        
        if msg_type != "handshake":
            return {
                "error": "Se requiere mensaje de handshake inicial",
                "code": "HANDSHAKE_REQUIRED",
                "expected": {
                    "type": "handshake",
                    "user_id": "int",
                    "external_activity_id": "int"
                }
            }
        
        user_id = data.get("user_id")
        external_activity_id = data.get("external_activity_id")
        company_id = data.get("company_id")
        
        if user_id is None or external_activity_id is None:
            return {
                "error": "Campos requeridos faltantes en handshake",
                "code": "MISSING_FIELDS",
                "required": ["user_id", "external_activity_id"]
            }
        
        try:
            user_id = int(user_id)
            external_activity_id = int(external_activity_id)
        except (ValueError, TypeError):
            return {
                "error": "user_id y external_activity_id deben ser enteros",
                "code": "INVALID_FIELD_TYPE"
            }
        
        state.set_metadata(user_id, external_activity_id, company_id)
        
        print(f"[INFO] Handshake completado para actividad {state.activity_uuid}: user={user_id}, ext_activity={external_activity_id}")
        
        return {
            "type": "handshake_ack",
            "status": "ready",
            "activity_uuid": state.activity_uuid,
            "session_id": state.session_id
        }

    async def _handle_frame(self, state: ConnectionState, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        frame = BiometricFrameDTO.from_dict(data)

        use_case = ProcessBiometricFrameUseCase(
            db=self.db,
            buffer=state.buffer,
            context=state.context,
            activity_uuid=state.activity_uuid,
            session_id=state.session_id,
            user_id=state.metadata.user_id,
            external_activity_id=state.metadata.external_activity_id
        )
        result = use_case.execute(frame)

        evaluator = EvaluateInterventionResultUseCase(self.db)
        evaluator.execute(state.buffer)

        return result