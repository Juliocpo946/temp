import json
import uuid
import threading
import time
import pika
from typing import Optional, Dict, Any
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import (
    SESSION_CONFIG_REQUEST_QUEUE,
    RABBITMQ_TIMEOUT,
    MAX_RETRIES,
    CACHE_TTL,
    AMQP_URL
)


class SessionConfigClient:
    def __init__(self, rabbitmq_client, redis_client: Optional[RedisClient] = None):
        self.rabbitmq_client = rabbitmq_client
        self.redis_client = redis_client
        self._pending_requests: Dict[str, Optional[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self._response_consumer_started = False
        self._instance_id = str(uuid.uuid4())[:8]
        self._response_queue = f"session_config_response_{self._instance_id}"
        self._connection = None
        self._channel = None
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
        print(f"[SESSION_CONFIG_CLIENT] [INFO] Consumer de respuestas iniciado en cola: {self._response_queue}")

    def _consume_responses(self) -> None:
        while True:
            try:
                parameters = pika.URLParameters(AMQP_URL)
                parameters.heartbeat = 300
                parameters.blocked_connection_timeout = 150
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                
                self._channel.queue_declare(
                    queue=self._response_queue,
                    durable=False,
                    exclusive=False,
                    auto_delete=True
                )
                
                self._channel.basic_consume(
                    queue=self._response_queue,
                    on_message_callback=self._on_response,
                    auto_ack=True
                )
                
                self._channel.start_consuming()
            except Exception as e:
                print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error en consumer de respuestas: {str(e)}")
                time.sleep(5)

    def _on_response(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            correlation_id = message.get("correlation_id")

            if correlation_id in self._pending_requests:
                config = {
                    "cognitive_analysis_enabled": message.get("cognitive_analysis_enabled", True),
                    "text_notifications": message.get("text_notifications", True),
                    "video_suggestions": message.get("video_suggestions", True),
                    "vibration_alerts": message.get("vibration_alerts", True),
                    "pause_suggestions": message.get("pause_suggestions", True),
                    "is_default": False
                }
                
                with self._lock:
                    self._pending_requests[correlation_id] = config

                if self.redis_client:
                    session_id = message.get("session_id")
                    if session_id:
                        # CORRECCIÓN: Usar set_session_config en lugar de store_session_config
                        self.redis_client.set_session_config(session_id, config, ttl=CACHE_TTL)

        except Exception as e:
            print(f"[SESSION_CONFIG_CLIENT] [ERROR] Error procesando respuesta: {str(e)}")

    def get_session_config(self, session_id: str) -> Dict[str, Any]:
        if self.redis_client:
            cached = self.redis_client.get_session_config(session_id)
            if cached:
                return cached

        correlation_id = str(uuid.uuid4())

        with self._lock:
            self._pending_requests[correlation_id] = None

        request = {
            "session_id": session_id,
            "correlation_id": correlation_id,
            "reply_to": self._response_queue
        }

        success = self.rabbitmq_client.publish(
            SESSION_CONFIG_REQUEST_QUEUE,
            request,
            correlation_id=correlation_id
        )

        if not success:
            with self._lock:
                self._pending_requests.pop(correlation_id, None)
            return self._default_config

        start_time = time.time()
        while time.time() - start_time < RABBITMQ_TIMEOUT:
            with self._lock:
                response = self._pending_requests.get(correlation_id)
                if response is not None:
                    self._pending_requests.pop(correlation_id, None)
                    return response
            time.sleep(0.1)

        with self._lock:
            self._pending_requests.pop(correlation_id, None)

        print(f"[SESSION_CONFIG_CLIENT] [WARNING] Timeout, usando config por defecto para sesion: {session_id}")
        return self._default_config