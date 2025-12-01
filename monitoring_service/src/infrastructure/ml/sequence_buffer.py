from typing import Optional, List, Dict, Any
from collections import deque
import numpy as np
from src.infrastructure.config.settings import SEQUENCE_LENGTH

class SequenceBuffer:
    def __init__(self, max_length: int = SEQUENCE_LENGTH):
        self.max_length = max_length
        self.buffer: deque = deque(maxlen=max_length)
        self.raw_frames: deque = deque(maxlen=max_length)

    def add(self, features: np.ndarray, raw_frame: Dict[str, Any]) -> None:
        self.buffer.append(features)
        self.raw_frames.append(raw_frame)

    def is_ready(self) -> bool:
        return len(self.buffer) >= self.max_length

    def get_sequence(self) -> Optional[np.ndarray]:
        if not self.is_ready():
            return None
        return np.array(list(self.buffer), dtype=np.float32)

    def get_snapshot(self) -> List[Dict[str, Any]]:
        return list(self.raw_frames)

    def clear(self) -> None:
        self.buffer.clear()
        self.raw_frames.clear()

    def get_recent_frames(self, count: int) -> List[np.ndarray]:
        frames = list(self.buffer)
        return frames[-count:] if len(frames) >= count else frames

    def __len__(self) -> int:
        return len(self.buffer)