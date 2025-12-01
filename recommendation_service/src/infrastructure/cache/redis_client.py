import json
import hashlib
from typing import Optional, Dict, Any
from upstash_redis import Redis
from src.infrastructure.config.settings import REDIS_URL, REDIS_TOKEN


class RedisClient:
    def __init__(self):
        self.client = None
        if REDIS_URL and REDIS_TOKEN:
            try:
                self.client = Redis(url=REDIS_URL, token=REDIS_TOKEN)
                print(f"[REDIS_CLIENT] [INFO] Conectado a Redis")
            except Exception as e:
                print(f"[REDIS_CLIENT] [ERROR] Error conectando a Redis: {str(e)}")
                self.client = None

    def _is_available(self) -> bool:
        return self.client is not None

    def get_activity_details(self, activity_uuid: str) -> Optional[Dict[str, Any]]:
        if not self._is_available():
            return None
        try:
            key = f"activity_details:{activity_uuid}"
            data = self.client.get(key)
            if data:
                print(f"[REDIS_CLIENT] [INFO] Cache hit para actividad: {activity_uuid}")
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo detalles de actividad: {str(e)}")
            return None

    def set_activity_details(self, activity_uuid: str, data: Dict[str, Any], ttl: int = 600) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"activity_details:{activity_uuid}"
            self.client.setex(key, ttl, json.dumps(data))
            print(f"[REDIS_CLIENT] [INFO] Detalles de actividad cacheados: {activity_uuid}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error cacheando detalles de actividad: {str(e)}")
            return False

    def get_session_config(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self._is_available():
            return None
        try:
            key = f"session_config:{session_id}"
            data = self.client.get(key)
            if data:
                print(f"[REDIS_CLIENT] [INFO] Cache hit para config de sesion: {session_id}")
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo config de sesion: {str(e)}")
            return None

    def set_session_config(self, session_id: str, config: Dict[str, Any], ttl: int = 300) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"session_config:{session_id}"
            self.client.setex(key, ttl, json.dumps(config))
            print(f"[REDIS_CLIENT] [INFO] Config de sesion cacheada: {session_id}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error cacheando config de sesion: {str(e)}")
            return False

    def delete_session_config(self, session_id: str) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"session_config:{session_id}"
            self.client.delete(key)
            print(f"[REDIS_CLIENT] [INFO] Config de sesion eliminada: {session_id}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error eliminando config de sesion: {str(e)}")
            return False

    def _generate_content_key(
        self,
        topic: str,
        intervention_type: str,
        cognitive_event: str
    ) -> str:
        key_string = f"{topic}:{intervention_type}:{cognitive_event}"
        hash_value = hashlib.md5(key_string.encode()).hexdigest()
        return f"generated_content:{hash_value}"

    def get_generated_content(
        self,
        topic: str,
        intervention_type: str,
        cognitive_event: str
    ) -> Optional[str]:
        if not self._is_available():
            return None
        try:
            key = self._generate_content_key(topic, intervention_type, cognitive_event)
            content = self.client.get(key)
            if content:
                print(f"[REDIS_CLIENT] [INFO] Cache hit para contenido generado: {topic[:30]}...")
                return content
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo contenido generado: {str(e)}")
            return None

    def set_generated_content(
        self,
        topic: str,
        intervention_type: str,
        cognitive_event: str,
        content: str,
        ttl: int = 3600
    ) -> bool:
        if not self._is_available():
            return False
        try:
            key = self._generate_content_key(topic, intervention_type, cognitive_event)
            self.client.setex(key, ttl, content)
            print(f"[REDIS_CLIENT] [INFO] Contenido generado cacheado: {topic[:30]}...")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error cacheando contenido generado: {str(e)}")
            return False

    def increment_gemini_calls(self) -> int:
        if not self._is_available():
            return 0
        try:
            key = "gemini_rate_limit"
            count = self.client.incr(key)
            if count == 1:
                self.client.expire(key, 60)
            return count
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error incrementando rate limit: {str(e)}")
            return 0

    def get_gemini_calls_count(self) -> int:
        if not self._is_available():
            return 0
        try:
            count = self.client.get("gemini_rate_limit")
            return int(count) if count else 0
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo rate limit: {str(e)}")
            return 0

    def get_circuit_breaker_state(self, service: str) -> Optional[Dict[str, Any]]:
        if not self._is_available():
            return None
        try:
            key = f"circuit_breaker:{service}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo estado circuit breaker: {str(e)}")
            return None

    def set_circuit_breaker_state(self, service: str, state: Dict[str, Any], ttl: int = 300) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"circuit_breaker:{service}"
            self.client.setex(key, ttl, json.dumps(state))
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error guardando estado circuit breaker: {str(e)}")
            return False

    def close(self):
        pass