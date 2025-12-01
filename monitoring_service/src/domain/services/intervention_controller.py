from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import numpy as np
from src.domain.value_objects.intervention_type import InterventionType
from src.infrastructure.config.settings import (
    COOLDOWN_VIBRATION_SECONDS,
    COOLDOWN_INSTRUCTION_SECONDS,
    COOLDOWN_PAUSE_SECONDS
)


class SessionContext:
    def __init__(self):
        self.last_vibration_at: Optional[datetime] = None
        self.last_instruction_at: Optional[datetime] = None
        self.last_pause_at: Optional[datetime] = None
        self.vibration_count: int = 0
        self.instruction_count: int = 0
        self.pause_count: int = 0
        self.current_external_activity_id: Optional[int] = None
        self._session_id: Optional[str] = None
        self._activity_uuid: Optional[str] = None
        self._redis_client = None

    def set_redis_client(self, redis_client, session_id: str, activity_uuid: str) -> None:
        self._redis_client = redis_client
        self._session_id = session_id
        self._activity_uuid = activity_uuid

    def load_from_redis(self) -> bool:
        if not self._redis_client or not self._session_id or not self._activity_uuid:
            return False
        
        try:
            data = self._redis_client.get_cooldown_state(self._session_id, self._activity_uuid)
            if data:
                self.vibration_count = data.get("vibration_count", 0)
                self.instruction_count = data.get("instruction_count", 0)
                self.pause_count = data.get("pause_count", 0)
                self.current_external_activity_id = data.get("current_external_activity_id")
                
                if data.get("last_vibration_at"):
                    self.last_vibration_at = datetime.fromisoformat(data["last_vibration_at"])
                if data.get("last_instruction_at"):
                    self.last_instruction_at = datetime.fromisoformat(data["last_instruction_at"])
                if data.get("last_pause_at"):
                    self.last_pause_at = datetime.fromisoformat(data["last_pause_at"])
                
                print(f"[SESSION_CONTEXT] [INFO] Estado de cooldown cargado desde Redis")
                return True
            return False
        except Exception as e:
            print(f"[SESSION_CONTEXT] [ERROR] Error cargando cooldown desde Redis: {str(e)}")
            return False

    def save_to_redis(self) -> bool:
        if not self._redis_client or not self._session_id or not self._activity_uuid:
            return False
        
        try:
            data = {
                "vibration_count": self.vibration_count,
                "instruction_count": self.instruction_count,
                "pause_count": self.pause_count,
                "current_external_activity_id": self.current_external_activity_id,
                "last_vibration_at": self.last_vibration_at.isoformat() if self.last_vibration_at else None,
                "last_instruction_at": self.last_instruction_at.isoformat() if self.last_instruction_at else None,
                "last_pause_at": self.last_pause_at.isoformat() if self.last_pause_at else None
            }
            return self._redis_client.save_cooldown_state(self._session_id, self._activity_uuid, data)
        except Exception as e:
            print(f"[SESSION_CONTEXT] [ERROR] Error guardando cooldown en Redis: {str(e)}")
            return False

    def reset_for_activity(self, external_activity_id: int) -> None:
        if self.current_external_activity_id != external_activity_id:
            self.current_external_activity_id = external_activity_id
            self.vibration_count = 0
            self.instruction_count = 0
            self.pause_count = 0
            self.last_vibration_at = None
            self.last_instruction_at = None
            self.last_pause_at = None
            self.save_to_redis()

    def get_context_vector(self) -> np.ndarray:
        now = datetime.utcnow()
        max_time = 300.0
        
        time_since_vibration = max_time
        if self.last_vibration_at:
            time_since_vibration = min((now - self.last_vibration_at).total_seconds(), max_time)
        
        time_since_instruction = max_time
        if self.last_instruction_at:
            time_since_instruction = min((now - self.last_instruction_at).total_seconds(), max_time)
        
        time_since_pause = max_time
        if self.last_pause_at:
            time_since_pause = min((now - self.last_pause_at).total_seconds(), max_time)
        
        return np.array([
            time_since_vibration / max_time,
            time_since_instruction / max_time,
            time_since_pause / max_time,
            min(self.vibration_count / 10.0, 1.0),
            min(self.instruction_count / 5.0, 1.0),
            min(self.pause_count / 3.0, 1.0)
        ], dtype=np.float32)

    def get_snapshot(self) -> Dict[str, Any]:
        return {
            "vibration_count": self.vibration_count,
            "instruction_count": self.instruction_count,
            "pause_count": self.pause_count,
            "last_vibration_at": self.last_vibration_at.isoformat() if self.last_vibration_at else None,
            "last_instruction_at": self.last_instruction_at.isoformat() if self.last_instruction_at else None,
            "last_pause_at": self.last_pause_at.isoformat() if self.last_pause_at else None
        }

    def register_intervention(self, intervention_type: InterventionType) -> None:
        now = datetime.utcnow()
        if intervention_type == InterventionType.VIBRATION:
            self.last_vibration_at = now
            self.vibration_count += 1
        elif intervention_type == InterventionType.INSTRUCTION:
            self.last_instruction_at = now
            self.instruction_count += 1
        elif intervention_type == InterventionType.PAUSE:
            self.last_pause_at = now
            self.pause_count += 1
        
        self.save_to_redis()


class InterventionController:
    def __init__(self):
        self.cooldowns = {
            InterventionType.VIBRATION: timedelta(seconds=COOLDOWN_VIBRATION_SECONDS),
            InterventionType.INSTRUCTION: timedelta(seconds=COOLDOWN_INSTRUCTION_SECONDS),
            InterventionType.PAUSE: timedelta(seconds=COOLDOWN_PAUSE_SECONDS)
        }

    def is_cooldown_active(
        self,
        intervention_type: InterventionType,
        context: SessionContext
    ) -> bool:
        now = datetime.utcnow()
        cooldown = self.cooldowns.get(intervention_type)
        
        if not cooldown:
            return False
        
        last_time = None
        if intervention_type == InterventionType.VIBRATION:
            last_time = context.last_vibration_at
        elif intervention_type == InterventionType.INSTRUCTION:
            last_time = context.last_instruction_at
        elif intervention_type == InterventionType.PAUSE:
            last_time = context.last_pause_at
        
        if last_time is None:
            return False
        
        return (now - last_time) < cooldown

    def can_intervene(
        self,
        intervention_type: InterventionType,
        context: SessionContext
    ) -> bool:
        if intervention_type == InterventionType.NO_INTERVENTION:
            return False
        return not self.is_cooldown_active(intervention_type, context)