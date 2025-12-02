import json
import pika
import time
from typing import Dict, Any
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

            print(f"[RABBITMQ] Conectando a {self.url.split('@')[-1]}...")  # Log seguro sin password
            parameters = pika.URLParameters(self.url)
            # Heartbeat para mantener viva la conexión
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            print("[RABBITMQ] Conexión establecida exitosamente.")
        except Exception as e:
            print(f"[RABBITMQ] Error fatal conectando: {str(e)}")
            raise e

    def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Publica un mensaje asegurando que la conexión esté viva."""
        try:
            # 1. Asegurar conexión
            self._connect()

            # 2. Asegurar que la cola existe (Durable = True es importante)
            self.channel.queue_declare(queue=queue_name, durable=True)

            # 3. Publicar con persistencia (delivery_mode=2)
            self.channel.basic_publish(
                exchange='',  # Intercambio por defecto
                routing_key=queue_name,  # La ruta es el nombre de la cola
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente
                    content_type='application/json'
                )
            )
            print(f"[RABBITMQ] Mensaje publicado en '{queue_name}': {json.dumps(message)[:50]}...")
            return True

        except (pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed) as e:
            print(f"[RABBITMQ] Conexión perdida durante publicación: {e}. Reintentando una vez...")
            # Resetear conexión y reintentar una vez
            self.connection = None
            try:
                self._connect()
                self.channel.queue_declare(queue=queue_name, durable=True)
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                print(f"[RABBITMQ] Reintento exitoso en '{queue_name}'")
                return True
            except Exception as e2:
                print(f"[RABBITMQ] Falló el reintento: {e2}")
                return False

        except Exception as e:
            print(f"[RABBITMQ] Error no recuperable publicando: {str(e)}")
            return False

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()