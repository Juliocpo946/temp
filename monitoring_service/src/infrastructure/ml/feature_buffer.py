from typing import Optional, List, Dict, Any
from collections import deque
import numpy as np
from src.infrastructure.config.settings import FEATURE_BUFFER_SIZE

class FeatureBuffer:
    def __init__(self, max_length: int = FEATURE_BUFFER_SIZE):
        self.max_length = max_length
        self.buffer: deque = deque(maxlen=max_length)
        self.raw_frames: deque = deque(maxlen=max_length)

    def add(self, features: np.ndarray, raw_frame: Dict[str, Any]) -> None:
        self.buffer.append(features)
        self.raw_frames.append(raw_frame)

    def is_ready(self, min_samples: int = 50) -> bool:
        return len(self.buffer) >= min_samples

    def get_all_features(self) -> Optional[np.ndarray]:
        if not self.buffer:
            return None
        return np.array(list(self.buffer), dtype=np.float32)

    def get_recent_features(self, count: int) -> Optional[np.ndarray]:
        if len(self.buffer) < count:
            return None
        frames = list(self.buffer)[-count:]
        return np.array(frames, dtype=np.float32)

    def get_raw_frames(self, count: int) -> List[Dict[str, Any]]:
        frames = list(self.raw_frames)
        return frames[-count:] if len(frames) >= count else frames

    def get_all_raw_frames(self) -> List[Dict[str, Any]]:
        return list(self.raw_frames)

    def clear(self) -> None:
        self.buffer.clear()
        self.raw_frames.clear()

    def __len__(self) -> int:
        return len(self.buffer)