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

            print(f"[RABBITMQ] Conectando a RabbitMQ...")
            parameters = pika.URLParameters(self.url)
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            print("[RABBITMQ] Conexión establecida exitosamente.")
        except Exception as e:
            print(f"[RABBITMQ] Error fatal conectando: {str(e)}")
            raise e

    def declare_queue(self, queue_name: str) -> None:
        self._connect()
        # Durable=True es crucial para que coincida con la configuración de los otros servicios
        self.channel.queue_declare(queue=queue_name, durable=True)

    def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        """Publica un mensaje (Usado para enviar Emails)"""
        try:
            self._connect()
            self.declare_queue(queue_name)

            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            print(f"[RABBITMQ] Mensaje publicado en '{queue_name}': {str(message)[:50]}...")

        except (pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed) as e:
            print(f"[RABBITMQ] Conexión perdida al publicar. Reintentando... {e}")
            self.connection = None
            try:
                self._connect()
                self.declare_queue(queue_name)
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                print(f"[RABBITMQ] Reintento de publicación exitoso.")
            except Exception as e2:
                print(f"[RABBITMQ] Falló el reintento de publicación: {e2}")

    def consume(self, queue_name: str, callback: Callable) -> None:
        """Consume mensajes (Usado para recibir Pagos)"""
        try:
            self._connect()
            self.declare_queue(queue_name)

            # Prefetch=1 para distribuir carga equitativamente
            self.channel.basic_qos(prefetch_count=1)

            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
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