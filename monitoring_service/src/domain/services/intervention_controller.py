from typing import Dict, Any, Optional
from datetime import datetime, timedelta
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

    def reset_for_activity(self, external_activity_id: int) -> None:
        self.current_external_activity_id = external_activity_id
        self.vibration_count = 0
        self.instruction_count = 0
        self.pause_count = 0
        self.last_vibration_at = None
        self.last_instruction_at = None
        self.last_pause_at = None

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