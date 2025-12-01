import json
import threading
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import CACHE_INVALIDATION_QUEUE, LOG_SERVICE_QUEUE


class CacheInvalidationConsumer:
    def __init__(self, rabbitmq_client: RabbitMQClient, redis_client: RedisClient):
        self.rabbitmq_client = rabbitmq_client
        self.redis_client = redis_client

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_invalidations, daemon=True)
        thread.start()
        print(f"[CACHE_INVALIDATION_CONSUMER] [INFO] Consumer iniciado")

    def _consume_invalidations(self) -> None:
        try:
            self.rabbitmq_client.consume(CACHE_INVALIDATION_QUEUE, self._callback, with_dlq=False)
        except Exception as e:
            print(f"[CACHE_INVALIDATION_CONSUMER] [ERROR] Error en consumer: {str(e)}")

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