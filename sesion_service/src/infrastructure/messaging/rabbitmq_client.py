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
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
        except Exception as e:
            raise

    def declare_queue(self, queue_name: str) -> None:
        if self.channel is None or self.channel.is_closed:
            self.connect()
        self.channel.queue_declare(queue=queue_name, durable=True)

    def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
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
                return
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    try:
                        self.connect()
                    except:
                        pass
                else:
                    raise

    def close(self) -> None:
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            pass