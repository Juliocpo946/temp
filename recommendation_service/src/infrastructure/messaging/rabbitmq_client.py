import json
import pika
from typing import Dict, Any, Callable
from src.infrastructure.config.settings import AMQP_URL


class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self) -> None:
        try:
            parameters = pika.URLParameters(AMQP_URL)
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
        except Exception as e:
            raise RuntimeError(f"Error conectando a RabbitMQ: {str(e)}")

    def _ensure_connection(self) -> None:
        if self.connection is None or self.connection.is_closed:
            self._connect()
        if self.channel is None or self.channel.is_closed:
            self.channel = self.connection.channel()

    def declare_queue(self, queue_name: str) -> None:
        self._ensure_connection()
        self.channel.queue_declare(queue=queue_name, durable=True)

    def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                self._ensure_connection()
                self.declare_queue(queue_name)
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                return True
            except Exception:
                retry_count += 1
                if retry_count < max_retries:
                    try:
                        self._connect()
                    except Exception:
                        pass
                else:
                    return False
        return False

    def consume(self, queue_name: str, callback: Callable) -> None:
        try:
            self._ensure_connection()
            self.declare_queue(queue_name)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
            self.channel.start_consuming()
        except Exception as e:
            raise RuntimeError(f"Error consumiendo de RabbitMQ: {str(e)}")

    def close(self) -> None:
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception:
            pass