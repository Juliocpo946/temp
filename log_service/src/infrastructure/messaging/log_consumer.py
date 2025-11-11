import json
import threading
from datetime import datetime
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.persistence.repositories.log_repository_impl import LogRepositoryImpl
from src.domain.entities.log import Log

class LogConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.log_repository = LogRepositoryImpl()

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_logs, daemon=True)
        thread.start()

    def _consume_logs(self) -> None:
        self.rabbitmq_client.consume('logs', self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            
            log = Log(
                id=None,
                service=message.get('service', 'unknown'),
                level=message.get('level', 'info'),
                message=message.get('message', ''),
                timestamp=datetime.utcnow()
            )

            self.log_repository.save(log)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Error al procesar log: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)