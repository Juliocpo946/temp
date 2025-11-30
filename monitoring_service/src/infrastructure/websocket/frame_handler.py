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
            
            activity_uuid = state.activity_uuid
            
            if self.state_manager.is_paused(activity_uuid):
                return None
            
            frame = BiometricFrameDTO.from_dict(data)

            use_case = ProcessBiometricFrameUseCase(
                db=self.db,
                buffer=state.buffer,
                context=state.context,
                activity_uuid=activity_uuid
            )
            result = use_case.execute(frame)

            evaluator = EvaluateInterventionResultUseCase(self.db)
            evaluator.execute(state.buffer)

            return result

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON invalido: {e}")
            return {"error": "JSON invalido"}
        except Exception as e:
            print(f"[ERROR] Error procesando frame: {e}")
            return {"error": str(e)}