import json
import pika
from typing import Dict, Any
from src.infrastructure.config.settings import AMQP_URL

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self) -> None:
        try:
            parameters = pika.URLParameters(AMQP_URL)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            print(f"Conectado a RabbitMQ")
        except Exception as e:
            print(f"Error al conectar con RabbitMQ: {str(e)}")
            raise

    def declare_queue(self, queue_name: str) -> None:
        self.channel.queue_declare(queue=queue_name, durable=True)

    def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        try:
            self.declare_queue(queue_name)
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as e:
            print(f"Error al publicar mensaje en RabbitMQ: {str(e)}")
            raise

    def close(self) -> None:
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print(f"Desconectado de RabbitMQ")
        except Exception as e:
            print(f"Error al cerrar conexión RabbitMQ: {str(e)}")