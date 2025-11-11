import json
import threading
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.smtp_client import SMTPClient
from email_service.src.application.use_cases.send_email import SendEmailUseCase
import asyncio

class EmailConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.smtp_client = SMTPClient()

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_emails, daemon=True)
        thread.start()

    def _consume_emails(self) -> None:
        self.rabbitmq_client.consume('email_events', self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            asyncio.run(self._handle_email(message))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error al procesar email: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    async def _handle_email(self, message: dict) -> None:
        use_case = SendEmailUseCase(self.smtp_client)
        await use_case.execute(
            to_email=message.get('to_email'),
            subject=message.get('subject'),
            html_body=message.get('html_body')
        )