import json
from typing import Optional, Dict, Any, List
from upstash_redis import Redis
from src.infrastructure.config.settings import REDIS_URL, REDIS_TOKEN


class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.client = None
        if REDIS_URL and REDIS_TOKEN:
            try:
                self.client = Redis(url=REDIS_URL, token=REDIS_TOKEN)
                print(f"[REDIS_CLIENT] [INFO] Conectado a Redis")
            except Exception as e:
                print(f"[REDIS_CLIENT] [ERROR] Error conectando a Redis: {str(e)}")
                self.client = None
        self._initialized = True

    def _is_available(self) -> bool:
        return self.client is not None

    def register_connection(self, session_id: str, instance_id: str, activity_uuid: str) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"ws_connection:{session_id}"
            data = {
                "instance_id": instance_id,
                "activity_uuid": activity_uuid
            }
            self.client.setex(key, 3600, json.dumps(data))
            print(f"[REDIS_CLIENT] [INFO] Conexion registrada: session={session_id}, instance={instance_id}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error registrando conexion: {str(e)}")
            return False

    def unregister_connection(self, session_id: str) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"ws_connection:{session_id}"
            self.client.delete(key)
            print(f"[REDIS_CLIENT] [INFO] Conexion eliminada: session={session_id}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error eliminando conexion: {str(e)}")
            return False

    def get_connection_instance(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self._is_available():
            return None
        try:
            key = f"ws_connection:{session_id}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo conexion: {str(e)}")
            return None

    def publish_recommendation(self, session_id: str, recommendation: Dict[str, Any]) -> bool:
        if not self._is_available():
            return False
        try:
            channel = f"recommendations:{session_id}"
            self.client.publish(channel, json.dumps(recommendation))
            print(f"[REDIS_CLIENT] [INFO] Recomendacion publicada en canal: {channel}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error publicando recomendacion: {str(e)}")
            return False

    def close(self):
        pass