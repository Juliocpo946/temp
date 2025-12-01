import json
import uuid
import threading
import time
from typing import Optional, Dict, Any
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import (
    SESSION_CONFIG_REQUEST_QUEUE,
    RABBITMQ_TIMEOUT,
    MAX_RETRIES,
    CACHE_TTL
)


class SessionConfigClient:
    def __init__(self, rabbitmq_client: RabbitMQClient, redis_client: Optional[RedisClient] = None):
        self.rabbitmq_client = rabbitmq_client
        self.redis_client = redis_client
        self._pending_requests: Dict[str, Optional[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self._response_consumer_started = False
        self._instance_id = str(uuid.uuid4())[:8]
        self._response_queue = f"session_config_response_{self._instance_id}"
        self._default_config = {
            "cognitive_analysis_enabled": True,
            "text_notifications": True,
            "video_suggestions": True,
            "vibration_alerts": True,
            "pause_suggestions": True,
            "is_default": True
        }
        self._start_response_consumer()

    def _start_response_consumer(self) -> None:
        if self._response_consumer_started:
            return

        thread = threading.Thread(target=self._consume_responses, daemon=True)
        thread.start()
        self._response_consumer_started = True
        print(f"[SESSION_CONFIG_CLIENT] [INFO] Consumer de respuestas iniciado en cola: {self._response_queue}")

    def _consume_responses(self) -> None:
        try:
            self.rabbitmq_client.consume_exclusive(self._response_queue, self._handle_response)
        except Exception as e:
            print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error en consumer de respuestas: {e}")
            time.sleep(5)
            self._response_consumer_started = False
            self._start_response_consumer()

    def _handle_response(self, ch, method, properties, body) -> None:
        try:
            data = json.loads(body)
            correlation_id = data.get("correlation_id")

            if correlation_id and correlation_id in self._pending_requests:
                with self._lock:
                    self._pending_requests[correlation_id] = data

                session_id = data.get("session_id")
                if self.redis_client and session_id:
                    self._cache_config(session_id, data)

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error procesando respuesta: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _cache_config(self, session_id: str, config: Dict[str, Any]) -> None:
        if not self.redis_client:
            return
        try:
            cache_data = {
                "cognitive_analysis_enabled": config.get("cognitive_analysis_enabled", True),
                "text_notifications": config.get("text_notifications", True),
                "video_suggestions": config.get("video_suggestions", True),
                "vibration_alerts": config.get("vibration_alerts", True),
                "pause_suggestions": config.get("pause_suggestions", True)
            }
            self.redis_client.set_session_config(session_id, cache_data, CACHE_TTL)
        except Exception as e:
            print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error cacheando config: {e}")

    def _get_cached(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.redis_client:
            return None
        try:
            return self.redis_client.get_session_config(session_id)
        except Exception as e:
            print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error obteniendo cache: {e}")
            return None

    def get_session_config(self, session_id: str, timeout: float = None) -> Dict[str, Any]:
        if timeout is None:
            timeout = float(RABBITMQ_TIMEOUT)

        cached = self._get_cached(session_id)
        if cached:
            print(f"[SESSION_CONFIG_CLIENT] [INFO] Config obtenida de cache para sesion: {session_id}")
            return cached

        for attempt in range(MAX_RETRIES):
            result = self._request_with_timeout(session_id, timeout)
            if result and not result.get("is_default"):
                return result
            
            if attempt < MAX_RETRIES - 1:
                wait_time = (attempt + 1) * 0.5
                print(f"[SESSION_CONFIG_CLIENT] [INFO] Reintentando solicitud (intento {attempt + 2}/{MAX_RETRIES})")
                time.sleep(wait_time)

        print(f"[SESSION_CONFIG_CLIENT] [WARNING] Usando config por defecto para sesion: {session_id}")
        return self._default_config.copy()

    def _request_with_timeout(self, session_id: str, timeout: float) -> Optional[Dict[str, Any]]:
        correlation_id = str(uuid.uuid4())

        with self._lock:
            self._pending_requests[correlation_id] = None

        request = {
            "type": "session_config_request",
            "session_id": session_id,
            "correlation_id": correlation_id,
            "reply_to": self._response_queue
        }

        success = self.rabbitmq_client.publish(SESSION_CONFIG_REQUEST_QUEUE, request)
        if not success:
            with self._lock:
                del self._pending_requests[correlation_id]
            return None

        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._lock:
                if self._pending_requests.get(correlation_id) is not None:
                    response = self._pending_requests.pop(correlation_id)
                    return response
            time.sleep(0.05)

        with self._lock:
            if correlation_id in self._pending_requests:
                del self._pending_requests[correlation_id]

        print(f"[SESSION_CONFIG_CLIENT] [WARNING] Timeout esperando config para sesion: {session_id}")
        return None

    def invalidate_cache(self, session_id: str) -> bool:
        if not self.redis_client:
            return False
        try:
            return self.redis_client.delete_session_config(session_id)
        except Exception as e:
            print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error invalidando cache: {e}")
            return False