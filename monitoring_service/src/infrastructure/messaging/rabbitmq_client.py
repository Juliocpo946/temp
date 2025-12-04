import json
import pika
from typing import Dict, Any, Callable, Optional
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
            print(f"[RABBITMQ_CLIENT] [INFO] Conectado a RabbitMQ")
        except Exception as e:
            print(f"[RABBITMQ_CLIENT] [ERROR] Error conectando a RabbitMQ: {str(e)}")
            raise

    def _ensure_connection(self) -> None:
        if self.connection is None or self.connection.is_closed:
            self._connect()
        if self.channel is None or self.channel.is_closed:
            self.channel = self.connection.channel()

    def publish(
        self, 
        queue_name: str, 
        message: Dict[str, Any], 
        correlation_id: Optional[str] = None
    ) -> bool:
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                self._ensure_connection()
                
                properties = pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
                
                if correlation_id:
                    properties.correlation_id = correlation_id
                
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=properties
                )
                return True
            except Exception as e:
                retry_count += 1
                print(f"[RABBITMQ_CLIENT] [ERROR] Error publicando mensaje (intento {retry_count}/{max_retries}): {str(e)}")
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
            self.channel.basic_qos(prefetch_count=10)
            self.channel.basic_consume(
                queue=queue_name, 
                on_message_callback=callback, 
                auto_ack=False
            )
            print(f"[RABBITMQ_CLIENT] [INFO] Escuchando en cola: {queue_name}")
            self.channel.start_consuming()
        except Exception as e:
            print(f"[RABBITMQ_CLIENT] [ERROR] Error consumiendo de RabbitMQ: {str(e)}")
            raise

    def close(self) -> None:
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print(f"[RABBITMQ_CLIENT] [INFO] Desconectado de RabbitMQ")
        except Exception as e:
            print(f"[RABBITMQ_CLIENT] [ERROR] Error cerrando conexion: {str(e)}")