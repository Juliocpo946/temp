import json
import threading
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.cache.redis_client import RedisClient

class CacheInvalidationConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.redis_client = RedisClient()

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_invalidations, daemon=True)
        thread.start()

    def _consume_invalidations(self) -> None:
        self.rabbitmq_client.consume('cache_invalidation', self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            action = message.get('action')
            key = message.get('key')

            if action == 'delete' and key:
                if key.startswith('apikey:'):
                    key_value = key.replace('apikey:', '')
                    self.redis_client.delete_api_key(key_value)
                    print(f"Cache invalidado para key: {key_value[:20]}...")

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error al procesar invalidacion: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)