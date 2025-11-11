import json
import threading
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.smtp_client import SMTPClient
from src.infrastructure.config.settings import EMAIL_QUEUE, LOG_SERVICE_QUEUE
from src.application.use_cases.send_email import SendEmailUseCase
import asyncio

class EmailConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.smtp_client = SMTPClient()
        self.email_queue = EMAIL_QUEUE
        self.log_queue = LOG_SERVICE_QUEUE

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_emails, daemon=True)
        thread.start()

    def _consume_emails(self) -> None:
        self.rabbitmq_client.consume(self.email_queue, self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            asyncio.run(self._handle_email(message))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self._publish_log(f"Error al procesar email: {str(e)}", "error")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    async def _handle_email(self, message: dict) -> None:
        to_email = message.get('to_email')
        subject = message.get('subject')
        html_body = message.get('html_body')
        
        if not all([to_email, subject, html_body]):
            self._publish_log("Falta to_email, subject o html_body en mensaje", "error")
            raise ValueError("Falta campos requeridos")
        
        use_case = SendEmailUseCase(self.smtp_client)
        result = await use_case.execute(
            to_email=to_email,
            subject=subject,
            html_body=html_body
        )
        
        if result:
            self._publish_log(f"Email enviado a {to_email} - Asunto: {subject}", "info")
        else:
            self._publish_log(f"Fallo al enviar email a {to_email} - Asunto: {subject}", "error")

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'email-service',
            'level': level,
            'message': message
        }
        try:
            self.rabbitmq_client.publish(self.log_queue, log_message)
        except Exception as e:
            print(f"Error publicando log: {str(e)}")