import json
import pika
from typing import Any, Dict
from src.infrastructure.config.settings import AMQP_URL

class RabbitMQClient:
    def __init__(self):
        self._connection = None
        self._channel = None

    def _get_connection(self):
        if self._connection is None or self._connection.is_closed:
            params = pika.URLParameters(AMQP_URL)
            self._connection = pika.BlockingConnection(params)
        return self._connection

    def _get_channel(self):
        if self._channel is None or self._channel.is_closed:
            self._channel = self._get_connection().channel()
        return self._channel

    def publish(self, queue: str, message: Dict[str, Any]) -> bool:
        try:
            channel = self._get_channel()
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )
            )
            return True
        except Exception as e:
            print(f"[ERROR] Error publicando mensaje: {e}")
            self._connection = None
            self._channel = None
            return False

    def close(self) -> None:
        try:
            if self._channel and not self._channel.is_closed:
                self._channel.close()
            if self._connection and not self._connection.is_closed:
                self._connection.close()
        except Exception as e:
            print(f"[ERROR] Error cerrando conexion RabbitMQ: {e}")
        finally:
            self._channel = None
            self._connection = None