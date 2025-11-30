import json
import uuid
import threading
import time
from typing import Optional, Dict, Any
from datetime import datetime
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import ACTIVITY_DETAILS_REQUEST_QUEUE, ACTIVITY_DETAILS_RESPONSE_QUEUE
from src.application.dtos.activity_details_dto import ActivityDetailsRequestDTO, ActivityDetailsResponseDTO


class ActivityDetailsClient:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.rabbitmq_client = rabbitmq_client
        self._pending_requests: Dict[str, Optional[ActivityDetailsResponseDTO]] = {}
        self._lock = threading.Lock()
        self._response_consumer_started = False
        self._start_response_consumer()

    def _start_response_consumer(self) -> None:
        if self._response_consumer_started:
            return
        
        thread = threading.Thread(target=self._consume_responses, daemon=True)
        thread.start()
        self._response_consumer_started = True
        print(f"[ACTIVITY_DETAILS_CLIENT] [INFO] Consumer de respuestas iniciado")

    def _consume_responses(self) -> None:
        try:
            self.rabbitmq_client.consume(ACTIVITY_DETAILS_RESPONSE_QUEUE, self._handle_response)
        except Exception as e:
            print(f"[ACTIVITY_DETAILS_CLIENT] [ERROR] Error en consumer de respuestas: {e}")

    def _handle_response(self, ch, method, properties, body) -> None:
        try:
            data = json.loads(body)
            correlation_id = data.get("correlation_id")
            
            if correlation_id and correlation_id in self._pending_requests:
                response = ActivityDetailsResponseDTO.from_dict(data)
                with self._lock:
                    self._pending_requests[correlation_id] = response
                print(f"[ACTIVITY_DETAILS_CLIENT] [INFO] Respuesta recibida para correlation_id: {correlation_id}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[ACTIVITY_DETAILS_CLIENT] [ERROR] Error procesando respuesta: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def get_activity_details(self, activity_uuid: str, timeout: float = 5.0) -> Optional[ActivityDetailsResponseDTO]:
        correlation_id = str(uuid.uuid4())
        
        with self._lock:
            self._pending_requests[correlation_id] = None

        request = ActivityDetailsRequestDTO(
            activity_uuid=activity_uuid,
            correlation_id=correlation_id
        )

        success = self.rabbitmq_client.publish(
            ACTIVITY_DETAILS_REQUEST_QUEUE,
            request.to_dict()
        )

        if not success:
            print(f"[ACTIVITY_DETAILS_CLIENT] [ERROR] No se pudo publicar solicitud para actividad: {activity_uuid}")
            with self._lock:
                del self._pending_requests[correlation_id]
            return None

        print(f"[ACTIVITY_DETAILS_CLIENT] [INFO] Solicitud enviada para actividad: {activity_uuid}")

        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._lock:
                response = self._pending_requests.get(correlation_id)
                if response is not None:
                    del self._pending_requests[correlation_id]
                    return response
            time.sleep(0.1)

        with self._lock:
            if correlation_id in self._pending_requests:
                del self._pending_requests[correlation_id]

        print(f"[ACTIVITY_DETAILS_CLIENT] [ERROR] Timeout esperando respuesta para actividad: {activity_uuid}")
        return None