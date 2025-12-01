import json
import asyncio
import threading
import pika
import time
import uuid
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from src.infrastructure.config.settings import (
    RECOMMENDATIONS_QUEUE,
    LOG_SERVICE_QUEUE,
    AMQP_URL,
    RECOMMENDATION_CONSUMER_WORKERS,
    RECOMMENDATION_PREFETCH_COUNT
)
from src.infrastructure.websocket.connection_manager import ConnectionManager
from src.infrastructure.cache.redis_client import RedisClient


class RecommendationConsumer:
    MAX_RETRY_COUNT = 5
    RETRY_DELAY_BASE = 1.0
    MESSAGE_TTL_SECONDS = 300

    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.redis_client = RedisClient()
        self.executor = ThreadPoolExecutor(max_workers=RECOMMENDATION_CONSUMER_WORKERS)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._connection = None
        self._channel = None
        self._publish_connection = None
        self._publish_channel = None
        self._max_retries = 3
        self._retry_delay = 1.0

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def start(self) -> None:
        self._running = True
        thread = threading.Thread(target=self._consume_recommendations, daemon=True)
        thread.start()
        print(f"[RECOMMENDATION_CONSUMER] [INFO] Consumer iniciado con {RECOMMENDATION_CONSUMER_WORKERS} workers")

    def _get_publish_channel(self):
        try:
            if self._publish_connection is None or self._publish_connection.is_closed:
                parameters = pika.URLParameters(AMQP_URL)
                self._publish_connection = pika.BlockingConnection(parameters)
            if self._publish_channel is None or self._publish_channel.is_closed:
                self._publish_channel = self._publish_connection.channel()
            return self._publish_channel
        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error obteniendo canal de publicacion: {str(e)}")
            return None

    def _consume_recommendations(self) -> None:
        while self._running:
            try:
                parameters = pika.URLParameters(AMQP_URL)
                parameters.heartbeat = 600
                parameters.blocked_connection_timeout = 300
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()

                self._channel.queue_declare(queue=RECOMMENDATIONS_QUEUE, durable=True)
                
                dlq_name = f"{RECOMMENDATIONS_QUEUE}_dlq"
                self._channel.queue_declare(queue=dlq_name, durable=True)
                
                self._channel.basic_qos(prefetch_count=RECOMMENDATION_PREFETCH_COUNT)

                self._channel.basic_consume(
                    queue=RECOMMENDATIONS_QUEUE,
                    on_message_callback=self._on_message,
                    auto_ack=False
                )

                print(f"[RECOMMENDATION_CONSUMER] [INFO] Escuchando en cola: {RECOMMENDATIONS_QUEUE}")
                self._channel.start_consuming()

            except Exception as e:
                print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error en consumer: {str(e)}")
                if self._running:
                    time.sleep(5)

    def _on_message(self, ch, method, properties, body) -> None:
        self.executor.submit(self._process_message, ch, method, properties, body)

    def _process_message(self, ch, method, properties, body) -> None:
        message_id = None
        try:
            message = json.loads(body)
            session_id = message.get("session_id")
            message_id = message.get("message_id") or str(uuid.uuid4())
            message["message_id"] = message_id

            if not session_id:
                print(f"[RECOMMENDATION_CONSUMER] [WARNING] Mensaje sin session_id")
                self._safe_ack(ch, method.delivery_tag)
                return

            retry_count = self.redis_client.get_message_retry_count(message_id)
            if retry_count >= self.MAX_RETRY_COUNT:
                print(f"[RECOMMENDATION_CONSUMER] [WARNING] Mensaje excedio max reintentos, enviando a DLQ: {message_id}")
                self._send_to_dlq(message)
                self._safe_ack(ch, method.delivery_tag)
                return

            states = self.connection_manager.get_all_states_by_session_id(session_id)

            if not states:
                target_instance = self.redis_client.get_target_instance_for_session(session_id)
                local_instance = self.redis_client.get_instance_id()

                if target_instance and target_instance != local_instance:
                    success = self.redis_client.publish_to_instance(target_instance, message)
                    if success:
                        print(f"[RECOMMENDATION_CONSUMER] [INFO] Mensaje reenviado via Redis Pub/Sub a instancia: {target_instance}")
                        self._safe_ack(ch, method.delivery_tag)
                        return

                self.redis_client.increment_message_retry(message_id)
                
                if retry_count < 3:
                    print(f"[RECOMMENDATION_CONSUMER] [INFO] No hay conexiones locales, requeue (intento {retry_count + 1})")
                    time.sleep(self.RETRY_DELAY_BASE * (retry_count + 1))
                    self._safe_nack(ch, method.delivery_tag, requeue=True)
                else:
                    print(f"[RECOMMENDATION_CONSUMER] [WARNING] Almacenando recomendacion pendiente para sesion: {session_id}")
                    self.redis_client.store_pending_recommendation(session_id, message, self.MESSAGE_TTL_SECONDS)
                    self._safe_ack(ch, method.delivery_tag)
                return

            recommendation_message = json.dumps({
                "type": "recommendation",
                "session_id": session_id,
                "user_id": message.get("user_id"),
                "action": message.get("action"),
                "content": message.get("content"),
                "vibration": message.get("vibration"),
                "metadata": message.get("metadata"),
                "timestamp": message.get("timestamp")
            })

            sent_count = 0
            failed_count = 0

            for state in states:
                if state.is_ready:
                    success = self._send_to_websocket_with_confirmation(state, recommendation_message)
                    if success:
                        sent_count += 1
                        self.redis_client.track_websocket_metric("sent", state.activity_uuid)
                    else:
                        failed_count += 1
                        self.redis_client.track_websocket_metric("failed", state.activity_uuid)

            if sent_count > 0:
                print(f"[RECOMMENDATION_CONSUMER] [INFO] Recomendacion enviada a {sent_count}/{len(states)} conexiones")
                self._safe_ack(ch, method.delivery_tag)
            elif failed_count > 0 and sent_count == 0:
                self.redis_client.increment_message_retry(message_id)
                if retry_count < self.MAX_RETRY_COUNT - 1:
                    print(f"[RECOMMENDATION_CONSUMER] [WARNING] Fallo envio a todas las conexiones, requeue")
                    self._safe_nack(ch, method.delivery_tag, requeue=True)
                else:
                    print(f"[RECOMMENDATION_CONSUMER] [WARNING] Fallo envio, enviando a DLQ")
                    self._send_to_dlq(message)
                    self._safe_ack(ch, method.delivery_tag)
            else:
                self._safe_ack(ch, method.delivery_tag)

        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error procesando recomendacion: {str(e)}")
            if message_id:
                self.redis_client.increment_message_retry(message_id)
            self._safe_nack(ch, method.delivery_tag, requeue=True)

    def _send_to_websocket_with_confirmation(self, state, message: str) -> bool:
        for attempt in range(self._max_retries):
            success = self._send_to_websocket_sync(state, message)
            if success:
                return True

            if attempt < self._max_retries - 1:
                delay = self._retry_delay * (attempt + 1)
                time.sleep(delay)
                print(f"[RECOMMENDATION_CONSUMER] [INFO] Reintentando envio (intento {attempt + 2}/{self._max_retries})")

        return False

    def _send_to_websocket_sync(self, state, message: str) -> bool:
        try:
            if self._loop is None:
                print(f"[RECOMMENDATION_CONSUMER] [ERROR] Event loop no configurado")
                return False

            if not self._loop.is_running():
                print(f"[RECOMMENDATION_CONSUMER] [ERROR] Event loop no esta corriendo")
                return False

            future = asyncio.run_coroutine_threadsafe(
                self._async_send_with_timeout(state.websocket, message),
                self._loop
            )
            
            result = future.result(timeout=15.0)
            
            if result:
                print(f"[RECOMMENDATION_CONSUMER] [INFO] Recomendacion enviada a actividad: {state.activity_uuid}")
            
            return result

        except asyncio.TimeoutError:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Timeout enviando por WebSocket")
            return False
        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error enviando por WebSocket: {str(e)}")
            return False

    async def _async_send_with_timeout(self, websocket, message: str) -> bool:
        try:
            await asyncio.wait_for(
                websocket.send_text(message),
                timeout=10.0
            )
            return True
        except asyncio.TimeoutError:
            return False
        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error en async send: {str(e)}")
            return False

    def _send_to_dlq(self, message: Dict[str, Any]) -> None:
        try:
            channel = self._get_publish_channel()
            if channel:
                dlq_name = f"{RECOMMENDATIONS_QUEUE}_dlq"
                message["dlq_reason"] = "max_retries_exceeded"
                message["dlq_timestamp"] = time.time()
                channel.basic_publish(
                    exchange='',
                    routing_key=dlq_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                print(f"[RECOMMENDATION_CONSUMER] [INFO] Mensaje enviado a DLQ: {dlq_name}")
        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error enviando a DLQ: {str(e)}")

    def _safe_ack(self, ch, delivery_tag) -> None:
        try:
            if ch.is_open:
                ch.basic_ack(delivery_tag=delivery_tag)
        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error en ack: {str(e)}")

    def _safe_nack(self, ch, delivery_tag, requeue: bool = True) -> None:
        try:
            if ch.is_open:
                ch.basic_nack(delivery_tag=delivery_tag, requeue=requeue)
        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error en nack: {str(e)}")

    def _log(self, message: str, level: str = "info") -> None:
        try:
            channel = self._get_publish_channel()
            if channel:
                log_message = {
                    "service": "monitoring-service",
                    "level": level,
                    "message": message
                }
                channel.basic_publish(
                    exchange='',
                    routing_key=LOG_SERVICE_QUEUE,
                    body=json.dumps(log_message)
                )
        except Exception:
            pass

    def close(self) -> None:
        self._running = False
        self.executor.shutdown(wait=False)
        try:
            if self._channel and self._channel.is_open:
                self._channel.stop_consuming()
            if self._connection and self._connection.is_open:
                self._connection.close()
            if self._publish_connection and self._publish_connection.is_open:
                self._publish_connection.close()
        except Exception as e:
            print(f"[RECOMMENDATION_CONSUMER] [ERROR] Error cerrando consumer: {str(e)}")
        print(f"[RECOMMENDATION_CONSUMER] [INFO] Consumer de recomendaciones cerrado")