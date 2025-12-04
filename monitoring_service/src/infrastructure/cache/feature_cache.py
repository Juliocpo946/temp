from typing import Optional, List
import json
import numpy as np
from src.infrastructure.cache.redis_client import RedisClient

class FeatureCache:
    def __init__(self):
        self.redis_client = RedisClient()
        self.ttl = 600

    def save_features(
        self,
        session_id: str,
        activity_uuid: str,
        features: np.ndarray
    ) -> bool:
        if not self.redis_client._is_available():
            return False

        try:
            key = f"features:{session_id}:{activity_uuid}"
            
            existing = self.redis_client.client.get(key)
            if existing:
                feature_list = json.loads(existing)
            else:
                feature_list = []

            feature_list.append(features.tolist())

            if len(feature_list) > 300:
                feature_list = feature_list[-300:]

            self.redis_client.client.setex(key, self.ttl, json.dumps(feature_list))
            return True
        except Exception as e:
            print(f"[FEATURE_CACHE] [ERROR] Error guardando features: {str(e)}")
            return False

    def get_features(
        self,
        session_id: str,
        activity_uuid: str,
        count: Optional[int] = None
    ) -> Optional[np.ndarray]:
        if not self.redis_client._is_available():
            return None

        try:
            key = f"features:{session_id}:{activity_uuid}"
            data = self.redis_client.client.get(key)
            
            if not data:
                return None

            feature_list = json.loads(data)
            
            if count:
                feature_list = feature_list[-count:]

            return np.array(feature_list, dtype=np.float32)
        except Exception as e:
            print(f"[FEATURE_CACHE] [ERROR] Error obteniendo features: {str(e)}")
            return None

    def clear_features(self, session_id: str, activity_uuid: str) -> bool:
        if not self.redis_client._is_available():
            return False

        try:
            key = f"features:{session_id}:{activity_uuid}"
            self.redis_client.client.delete(key)
            return True
        except Exception as e:
            print(f"[FEATURE_CACHE] [ERROR] Error limpiando features: {str(e)}")
            return False