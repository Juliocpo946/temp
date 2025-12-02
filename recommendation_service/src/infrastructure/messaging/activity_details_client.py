import json
import uuid
import threading
import time
import pika
from typing import Optional, Dict, Any
from datetime import datetime
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import (
    ACTIVITY_DETAILS_REQUEST_QUEUE,
    ACTIVITY_DETAILS_CACHE_TTL,
    RABBITMQ_TIMEOUT,
    MAX_RETRIES,
    AMQP_URL
)
from src.application.dtos.activity_details_dto import ActivityDetailsRequestDTO, ActivityDetailsResponseDTO


class ActivityDetailsClient:
    def __init__(self, rabbitmq_client, redis_client: Optional[RedisClient] = None):
        self.rabbitmq_client = rabbitmq_client
        self.redis_client = redis_client
        self._pending_requests: Dict[str, Optional[ActivityDetailsResponseDTO]] = {}
        self._lock = threading.Lock()
        self._response_consumer_started = False
        self._instance_id = str(uuid.uuid4())[:8]
        self._response_queue = f"activity_details_response_{self._instance_id}"
        self._connection = None
        self._channel = None
        self._start_response_consumer()

    def _start_response_consumer(self) -> None:
        if self._response_consumer_started:
            return

        thread = threading.Thread(target=self._consume_responses, daemon=True)
        thread.start()
        self._response_consumer_started = True
        print(f"[ACTIVITY_DETAILS_CLIENT] [INFO] Consumer de respuestas iniciado en cola: {self._response_queue}")

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
                print(f"[ACTIVITY_DETAILS_CLIENT] [ERROR] Error en consumer de respuestas: {str(e)}")
                time.sleep(5)

    def _on_response(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            correlation_id = message.get("correlation_id")

            if correlation_id in self._pending_requests:
                response_dto = ActivityDetailsResponseDTO(
                    activity_uuid=message.get("activity_uuid"),
                    title=message.get("title"),
                    subtitle=message.get("subtitle"),
                    content=message.get("content"),
                    activity_type=message.get("activity_type")
                )
                
                with self._lock:
                    self._pending_requests[correlation_id] = response_dto

                if self.redis_client and response_dto.activity_uuid:
                    self.redis_client.store_activity_details(
                        response_dto.activity_uuid,
                        response_dto.to_dict(),
                        ttl=ACTIVITY_DETAILS_CACHE_TTL
                    )

        except Exception as e:
            print(f"[ACTIVITY_DETAILS_CLIENT] [ERROR] Error procesando respuesta: {str(e)}")

    def request_activity_details(self, activity_uuid: str) -> Optional[ActivityDetailsResponseDTO]:
        if self.redis_client:
            cached = self.redis_client.get_activity_details(activity_uuid)
            if cached:
                return ActivityDetailsResponseDTO.from_dict(cached)

        correlation_id = str(uuid.uuid4())
        
        request = ActivityDetailsRequestDTO(
            activity_uuid=activity_uuid,
            correlation_id=correlation_id
        )

        with self._lock:
            self._pending_requests[correlation_id] = None

        success = self.rabbitmq_client.publish(
            ACTIVITY_DETAILS_REQUEST_QUEUE,
            {
                **request.to_dict(),
                "reply_to": self._response_queue
            },
            correlation_id=correlation_id
        )

        if not success:
            with self._lock:
                self._pending_requests.pop(correlation_id, None)
            return None

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

        print(f"[ACTIVITY_DETAILS_CLIENT] [ERROR] Timeout esperando respuesta para actividad: {activity_uuid}")
        return None