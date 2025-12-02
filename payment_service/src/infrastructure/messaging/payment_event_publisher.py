from typing import Optional
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import PAYMENT_EVENTS_QUEUE, LOG_SERVICE_QUEUE


class PaymentEventPublisher:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.rabbitmq_client = rabbitmq_client

    def publish_application_paid(self, application_id: str, company_id: str, amount: float) -> bool:
        message = {
            "type": "application_paid",
            "application_id": str(application_id),
            "company_id": str(company_id),
            "amount": amount,
            "currency": "mxn"
        }
        success = self.rabbitmq_client.publish(PAYMENT_EVENTS_QUEUE, message)

        if success:
            self._log(f"Evento de pago publicado para app: {application_id}")
        else:
            self._log(f"Error publicando evento de pago para app: {application_id}", "error")

        return success

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "payment-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)