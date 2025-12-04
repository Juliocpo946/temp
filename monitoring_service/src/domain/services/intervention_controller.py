from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from src.domain.value_objects.intervention_type import InterventionType
from src.infrastructure.config.settings import (
    COOLDOWN_VIBRATION_BASE,
    COOLDOWN_INSTRUCTION_BASE,
    COOLDOWN_PAUSE_BASE,
    COOLDOWN_EFFECTIVENESS_MULTIPLIER
)

class SessionContext:
    def __init__(self):
        self.last_vibration_at: Optional[datetime] = None
        self.last_instruction_at: Optional[datetime] = None
        self.last_pause_at: Optional[datetime] = None
        self.vibration_count: int = 0
        self.instruction_count: int = 0
        self.pause_count: int = 0
        self.vibration_effectiveness: float = 0.5
        self.instruction_effectiveness: float = 0.5
        self.pause_effectiveness: float = 0.5
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
                self.vibration_effectiveness = data.get("vibration_effectiveness", 0.5)
                self.instruction_effectiveness = data.get("instruction_effectiveness", 0.5)
                self.pause_effectiveness = data.get("pause_effectiveness", 0.5)
                self.current_external_activity_id = data.get("current_external_activity_id")
                
                if data.get("last_vibration_at"):
                    self.last_vibration_at = datetime.fromisoformat(data["last_vibration_at"])
                if data.get("last_instruction_at"):
                    self.last_instruction_at = datetime.fromisoformat(data["last_instruction_at"])
                if data.get("last_pause_at"):
                    self.last_pause_at = datetime.fromisoformat(data["last_pause_at"])
                
                print(f"[SESSION_CONTEXT] [INFO] Estado cargado desde Redis")
                return True
            return False
        except Exception as e:
            print(f"[SESSION_CONTEXT] [ERROR] Error cargando desde Redis: {str(e)}")
            return False

    def save_to_redis(self) -> bool:
        if not self._redis_client or not self._session_id or not self._activity_uuid:
            return False
        
        try:
            data = {
                "vibration_count": self.vibration_count,
                "instruction_count": self.instruction_count,
                "pause_count": self.pause_count,
                "vibration_effectiveness": self.vibration_effectiveness,
                "instruction_effectiveness": self.instruction_effectiveness,
                "pause_effectiveness": self.pause_effectiveness,
                "current_external_activity_id": self.current_external_activity_id,
                "last_vibration_at": self.last_vibration_at.isoformat() if self.last_vibration_at else None,
                "last_instruction_at": self.last_instruction_at.isoformat() if self.last_instruction_at else None,
                "last_pause_at": self.last_pause_at.isoformat() if self.last_pause_at else None
            }
            return self._redis_client.save_cooldown_state(self._session_id, self._activity_uuid, data)
        except Exception as e:
            print(f"[SESSION_CONTEXT] [ERROR] Error guardando en Redis: {str(e)}")
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

    def get_intervention_counts(self) -> Dict[str, int]:
        return {
            "vibration": self.vibration_count,
            "instruction": self.instruction_count,
            "pause": self.pause_count
        }

    def get_effectiveness_history(self) -> Dict[str, float]:
        return {
            "vibration": self.vibration_effectiveness,
            "instruction": self.instruction_effectiveness,
            "pause": self.pause_effectiveness
        }

    def record_intervention(self, intervention_type: InterventionType) -> None:
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

    def update_effectiveness(self, intervention_type: str, score: float) -> None:
        if intervention_type == "vibration":
            self.vibration_effectiveness = (self.vibration_effectiveness + score) / 2
        elif intervention_type == "instruction":
            self.instruction_effectiveness = (self.instruction_effectiveness + score) / 2
        elif intervention_type == "pause":
            self.pause_effectiveness = (self.pause_effectiveness + score) / 2
        
        self.save_to_redis()


class InterventionController:
    def __init__(self):
        self.base_cooldowns = {
            InterventionType.VIBRATION: timedelta(seconds=COOLDOWN_VIBRATION_BASE),
            InterventionType.INSTRUCTION: timedelta(seconds=COOLDOWN_INSTRUCTION_BASE),
            InterventionType.PAUSE: timedelta(seconds=COOLDOWN_PAUSE_BASE)
        }

    def is_cooldown_active(
        self,
        intervention_type: InterventionType,
        context: SessionContext
    ) -> bool:
        now = datetime.utcnow()
        
        cooldown = self._calculate_adaptive_cooldown(intervention_type, context)
        
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

    def _calculate_adaptive_cooldown(
        self,
        intervention_type: InterventionType,
        context: SessionContext
    ) -> timedelta:
        base_cooldown = self.base_cooldowns.get(intervention_type)
        if not base_cooldown:
            return timedelta(seconds=30)
        
        effectiveness = 0.5
        if intervention_type == InterventionType.VIBRATION:
            effectiveness = context.vibration_effectiveness
        elif intervention_type == InterventionType.INSTRUCTION:
            effectiveness = context.instruction_effectiveness
        elif intervention_type == InterventionType.PAUSE:
            effectiveness = context.pause_effectiveness
        
        multiplier = 1.0 + (COOLDOWN_EFFECTIVENESS_MULTIPLIER * (1.0 - effectiveness))
        
        adaptive_seconds = int(base_cooldown.total_seconds() * multiplier)
        return timedelta(seconds=adaptive_seconds)

    def can_intervene(
        self,
        intervention_type: InterventionType,
        context: SessionContext
    ) -> bool:
        if intervention_type == InterventionType.NO_INTERVENTION:
            return False
        return not self.is_cooldown_active(intervention_type, context)