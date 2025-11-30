import json
import pika
from typing import Callable, Dict, Any
from src.infrastructure.config.settings import AMQP_URL

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self) -> None:
        try:
            parameters = pika.URLParameters(AMQP_URL)
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            print(f"[RABBITMQ_CLIENT] [INFO] Conectado a RabbitMQ")
        except Exception as e:
            print(f"[RABBITMQ_CLIENT] [ERROR] Error al conectar con RabbitMQ: {str(e)}")
            raise

    def declare_queue(self, queue_name: str) -> None:
        if self.channel is None or self.channel.is_closed:
            self.connect()
        self.channel.queue_declare(queue=queue_name, durable=True)

    def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if self.connection is None or self.connection.is_closed:
                    self.connect()
                
                self.declare_queue(queue_name)
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                return True
            except Exception as e:
                retry_count += 1
                print(f"[RABBITMQ_CLIENT] [ERROR] Error al publicar mensaje (intento {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    try:
                        self.connect()
                    except:
                        pass
                else:
                    return False
        return False

    def consume(self, queue_name: str, callback: Callable) -> None:
        try:
            if self.connection is None or self.connection.is_closed:
                self.connect()
                
            self.declare_queue(queue_name)
            self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
            print(f"[RABBITMQ_CLIENT] [INFO] Escuchando en cola: {queue_name}")
            self.channel.start_consuming()
        except Exception as e:
            print(f"[RABBITMQ_CLIENT] [ERROR] Error al consumir de RabbitMQ: {str(e)}")
            raise

    def close(self) -> None:
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print(f"[RABBITMQ_CLIENT] [INFO] Desconectado de RabbitMQ")
        except Exception as e:
            print(f"[RABBITMQ_CLIENT] [ERROR] Error al cerrar conexion RabbitMQ: {str(e)}")