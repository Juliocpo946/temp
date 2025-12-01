import json
import hashlib
from typing import Optional, Dict, Any
from upstash_redis import Redis
from src.infrastructure.config.settings import (
    REDIS_URL, 
    REDIS_TOKEN,
    CACHE_TTL,
    ACTIVITY_DETAILS_CACHE_TTL,
    GENERATED_CONTENT_CACHE_TTL
)


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

    def set_activity_details(self, activity_uuid: str, data: Dict[str, Any], ttl: int = None) -> bool:
        if not self._is_available():
            return False
        try:
            if ttl is None:
                ttl = ACTIVITY_DETAILS_CACHE_TTL
            key = f"activity_details:{activity_uuid}"
            self.client.setex(key, ttl, json.dumps(data))
            print(f"[REDIS_CLIENT] [INFO] Detalles de actividad cacheados: {activity_uuid}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error cacheando detalles de actividad: {str(e)}")
            return False

    def delete_activity_details(self, activity_uuid: str) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"activity_details:{activity_uuid}"
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error eliminando cache de actividad: {str(e)}")
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

    def set_session_config(self, session_id: str, data: Dict[str, Any], ttl: int = None) -> bool:
        if not self._is_available():
            return False
        try:
            if ttl is None:
                ttl = CACHE_TTL
            key = f"session_config:{session_id}"
            self.client.setex(key, ttl, json.dumps(data))
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
            print(f"[REDIS_CLIENT] [INFO] Cache de config eliminado para sesion: {session_id}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error eliminando cache de config: {str(e)}")
            return False

    def get_generated_content(self, topic: str, content_type: str, cognitive_event: str) -> Optional[str]:
        if not self._is_available():
            return None
        try:
            cache_key = self._generate_content_key(topic, content_type, cognitive_event)
            key = f"generated_content:{cache_key}"
            data = self.client.get(key)
            if data:
                print(f"[REDIS_CLIENT] [INFO] Cache hit para contenido generado")
                return data
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo contenido generado: {str(e)}")
            return None

    def set_generated_content(self, topic: str, content_type: str, cognitive_event: str, content: str, ttl: int = None) -> bool:
        if not self._is_available():
            return False
        try:
            if ttl is None:
                ttl = GENERATED_CONTENT_CACHE_TTL
            cache_key = self._generate_content_key(topic, content_type, cognitive_event)
            key = f"generated_content:{cache_key}"
            self.client.setex(key, ttl, content)
            print(f"[REDIS_CLIENT] [INFO] Contenido generado cacheado")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error cacheando contenido generado: {str(e)}")
            return False

    def _generate_content_key(self, topic: str, content_type: str, cognitive_event: str) -> str:
        combined = f"{topic}:{content_type}:{cognitive_event}"
        return hashlib.md5(combined.encode()).hexdigest()

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

    def store_intervention_evaluation(self, intervention_id: str, evaluation: Dict[str, Any]) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"intervention_eval:{intervention_id}"
            self.client.setex(key, 86400, json.dumps(evaluation))
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error almacenando evaluacion: {str(e)}")
            return False

    def get_intervention_evaluations_for_topic(self, topic: str, limit: int = 10) -> list:
        if not self._is_available():
            return []
        try:
            pattern = f"intervention_eval:*"
            keys = self.client.keys(pattern)
            evaluations = []
            for key in keys[:limit * 2]:
                data = self.client.get(key)
                if data:
                    eval_data = json.loads(data)
                    if eval_data.get("topic") == topic:
                        evaluations.append(eval_data)
                        if len(evaluations) >= limit:
                            break
            return evaluations
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo evaluaciones: {str(e)}")
            return []

    def close(self):
        pass