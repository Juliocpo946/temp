import json
import threading
import pika
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import (
    CACHE_INVALIDATION_QUEUE,
    LOG_SERVICE_QUEUE,
    AMQP_URL
)


class CacheInvalidationConsumer:
    def __init__(self, rabbitmq_client, redis_client: RedisClient):
        self.rabbitmq_client = rabbitmq_client
        self.redis_client = redis_client
        self._connection = None
        self._channel = None

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_invalidations, daemon=True)
        thread.start()
        print(f"[CACHE_INVALIDATION_CONSUMER] [INFO] Consumer iniciado")

    def _consume_invalidations(self) -> None:
        while True:
            try:
                parameters = pika.URLParameters(AMQP_URL)
                parameters.heartbeat = 300
                parameters.blocked_connection_timeout = 150
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                
                self._channel.basic_qos(prefetch_count=10)
                self._channel.basic_consume(
                    queue=CACHE_INVALIDATION_QUEUE,
                    on_message_callback=self._callback,
                    auto_ack=False
                )
                
                print(f"[CACHE_INVALIDATION_CONSUMER] [INFO] Escuchando en cola: {CACHE_INVALIDATION_QUEUE}")
                self._channel.start_consuming()
            except Exception as e:
                print(f"[CACHE_INVALIDATION_CONSUMER] [ERROR] Error en consumer: {str(e)}")
                import time
                time.sleep(5)

    def _callback(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            action = message.get('action')
            session_id = message.get('session_id')
            key = message.get('key')

            if action == 'invalidate_session_config' and session_id:
                success = self.redis_client.delete_session_config(session_id)
                if success:
                    print(f"[CACHE_INVALIDATION_CONSUMER] [INFO] Cache de config invalidado para sesion: {session_id}")
                else:
                    print(f"[CACHE_INVALIDATION_CONSUMER] [WARNING] No se pudo invalidar cache para sesion: {session_id}")

            elif action == 'delete' and key:
                if key.startswith('activity_details:'):
                    activity_uuid = key.replace('activity_details:', '')
                    self.redis_client.delete_activity_details(activity_uuid)
                    print(f"[CACHE_INVALIDATION_CONSUMER] [INFO] Cache de actividad invalidado: {activity_uuid}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[CACHE_INVALIDATION_CONSUMER] [ERROR] Error procesando invalidacion: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "recommendation-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)