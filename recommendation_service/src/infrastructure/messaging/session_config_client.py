import json
import uuid
import threading
import time
from typing import Optional, Dict, Any
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import (
    SESSION_CONFIG_REQUEST_QUEUE,
    SESSION_CONFIG_RESPONSE_QUEUE
)


class SessionConfigClient:
    def __init__(self, rabbitmq_client: RabbitMQClient, redis_client: Optional[RedisClient] = None):
        self.rabbitmq_client = rabbitmq_client
        self.redis_client = redis_client
        self._pending_requests: Dict[str, Optional[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self._response_consumer_started = False
        self._default_config = {
            "cognitive_analysis_enabled": True,
            "text_notifications": True,
            "video_suggestions": True,
            "vibration_alerts": True,
            "pause_suggestions": True
        }
        self._start_response_consumer()

    def _start_response_consumer(self) -> None:
        if self._response_consumer_started:
            return

        thread = threading.Thread(target=self._consume_responses, daemon=True)
        thread.start()
        self._response_consumer_started = True
        print(f"[SESSION_CONFIG_CLIENT] [INFO] Consumer de respuestas iniciado")

    def _consume_responses(self) -> None:
        try:
            self.rabbitmq_client.consume(SESSION_CONFIG_RESPONSE_QUEUE, self._handle_response)
        except Exception as e:
            print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error en consumer de respuestas: {e}")

    def _handle_response(self, ch, method, properties, body) -> None:
        try:
            data = json.loads(body)
            correlation_id = data.get("correlation_id")

            if correlation_id and correlation_id in self._pending_requests:
                with self._lock:
                    self._pending_requests[correlation_id] = data

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error procesando respuesta: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def get_session_config(self, session_id: str, timeout: float = 3.0) -> Dict[str, Any]:
        if self.redis_client:
            cached = self.redis_client.get(f"session_config:{session_id}")
            if cached:
                try:
                    return json.loads(cached)
                except:
                    pass

        correlation_id = str(uuid.uuid4())

        with self._lock:
            self._pending_requests[correlation_id] = None

        request = {
            "type": "session_config_request",
            "session_id": session_id,
            "correlation_id": correlation_id
        }

        success = self.rabbitmq_client.publish(SESSION_CONFIG_REQUEST_QUEUE, request)
        if not success:
            print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error publicando solicitud de config")
            return self._default_config

        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._lock:
                if self._pending_requests.get(correlation_id) is not None:
                    response = self._pending_requests.pop(correlation_id)
                    config = {
                        "cognitive_analysis_enabled": response.get("cognitive_analysis_enabled", True),
                        "text_notifications": response.get("text_notifications", True),
                        "video_suggestions": response.get("video_suggestions", True),
                        "vibration_alerts": response.get("vibration_alerts", True),
                        "pause_suggestions": response.get("pause_suggestions", True)
                    }

                    if self.redis_client:
                        self.redis_client.setex(
                            f"session_config:{session_id}",
                            300,
                            json.dumps(config)
                        )

                    return config

            time.sleep(0.05)

        with self._lock:
            self._pending_requests.pop(correlation_id, None)

        print(f"[SESSION_CONFIG_CLIENT] [WARNING] Timeout obteniendo config, usando valores por defecto")
        return self._default_config