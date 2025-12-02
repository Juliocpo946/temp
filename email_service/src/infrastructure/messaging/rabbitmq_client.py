import json
import pika
import time
from typing import Callable, Dict, Any
from src.infrastructure.config.settings import AMQP_URL


class RabbitMQClient:
    def __init__(self):
        self.url = AMQP_URL
        self.connection = None
        self.channel = None

    def _connect(self):
        """Establece la conexión y el canal. Si falla, lanza excepción."""
        try:
            if self.connection and not self.connection.is_closed:
                return

            print(f"[RABBITMQ] Conectando a {self.url.split('@')[-1]}...")
            parameters = pika.URLParameters(self.url)
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            print("[RABBITMQ] Conexión establecida exitosamente.")
        except Exception as e:
            print(f"[RABBITMQ] Error conectando: {str(e)}")
            raise e

    def declare_queue(self, queue_name: str) -> None:
        self._connect()
        self.channel.queue_declare(queue=queue_name, durable=True)

    def publish(self, queue_name: str, message: dict) -> None:
        try:
            self._connect()
            self.declare_queue(queue_name)
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as e:
            print(f"[RABBITMQ] Error publicando mensaje: {str(e)}")

    def consume(self, queue_name: str, callback: Callable) -> None:
        """Inicia el consumo bloqueante. Debe ejecutarse en un hilo."""
        try:
            self._connect()
            self.declare_queue(queue_name)
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
            print(f"[RABBITMQ] Escuchando en cola: {queue_name}")
            self.channel.start_consuming()
        except Exception as e:
            print(f"[RABBITMQ] Error en consumo (posible desconexión): {str(e)}")
            self.close()
            raise e

    def close(self) -> None:
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception:
            pass