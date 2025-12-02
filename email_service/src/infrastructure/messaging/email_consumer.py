import json
import threading
import time
import asyncio
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.smtp_client import SMTPClient
from src.infrastructure.config.settings import EMAIL_QUEUE, LOG_SERVICE_QUEUE
from src.application.use_cases.send_email import SendEmailUseCase


class EmailConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.smtp_client = SMTPClient()
        self.email_queue = EMAIL_QUEUE
        self.log_queue = LOG_SERVICE_QUEUE
        self._running = False

    def start(self) -> None:
        self._running = True
        thread = threading.Thread(target=self._consume_loop, daemon=True)
        thread.start()
        print("[EMAIL_CONSUMER] Hilo de consumo iniciado.")

    def _consume_loop(self) -> None:
        while self._running:
            try:
                # Esto se bloquea escuchando. Si falla, el catch captura y reintenta.
                self.rabbitmq_client.consume(self.email_queue, self._callback)
            except Exception as e:
                print(f"[EMAIL_CONSUMER] Error crítico: {e}. Reintentando en 5s...")
                time.sleep(5)

    def _callback(self, ch, method, properties, body) -> None:
        try:
            print(f"[EMAIL_CONSUMER] Mensaje recibido: {body}")
            message = json.loads(body)

            # Ejecutar envío asíncrono
            asyncio.run(self._handle_email(message))

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[EMAIL_CONSUMER] Error procesando mensaje: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    async def _handle_email(self, message: dict) -> None:
        # (Tu lógica de envío existente)
        to_email = message.get('to_email')
        subject = message.get('subject')
        html_body = message.get('html_body')

        use_case = SendEmailUseCase(self.smtp_client)
        await use_case.execute(to_email, subject, html_body)