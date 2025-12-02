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
        """Establece la conexión y el canal de forma robusta."""
        try:
            if self.connection and not self.connection.is_closed:
                return

            print(f"[RABBITMQ] Conectando a RabbitMQ...")
            parameters = pika.URLParameters(self.url)
            # Ajustes para evitar desconexiones por inactividad
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            print("[RABBITMQ] Conexión establecida exitosamente.")
        except Exception as e:
            print(f"[RABBITMQ] Error fatal conectando: {str(e)}")
            # No relanzamos aquí para permitir reintentos en el bucle superior si es consumer
            raise e

    def declare_queue(self, queue_name: str) -> None:
        self._connect()
        # Durable=True es CRÍTICO. Si una app usa True y la otra False, fallará silenciosamente.
        self.channel.queue_declare(queue=queue_name, durable=True)

    def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        """Publica un mensaje con reintentos."""
        try:
            self._connect()
            self.declare_queue(queue_name)

            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensaje persistente
                    content_type='application/json'
                )
            )
            # Log detallado para confirmar qué salió
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
        except Exception as e:
            print(f"[RABBITMQ] Error no recuperable publicando: {str(e)}")

    def consume(self, queue_name: str, callback: Callable) -> None:
        """Inicia el consumo bloqueante."""
        try:
            self._connect()
            self.declare_queue(queue_name)

            # Prefetch=1 asegura que no se sature el consumidor
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