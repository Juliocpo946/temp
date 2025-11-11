from datetime import datetime
from src.domain.entities.request import Request
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.dtos.request_dto import RequestDTO

class RouteRequestUseCase:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.rabbitmq_client = rabbitmq_client

    def execute(self, correlation_id: str, token: str, service: str, method: str, path: str, status: int) -> None:
        request = Request(
            correlation_id=correlation_id,
            token=token,
            service=service,
            method=method,
            path=path,
            status=status,
            timestamp=datetime.utcnow()
        )

        request_dto = RequestDTO(
            correlation_id=request.correlation_id,
            token=request.token,
            service=request.service,
            method=request.method,
            path=request.path,
            status=request.status,
            timestamp=request.timestamp
        )

        self._publish_log(f"Petición ruteada: {method} {path} -> {service} [{status}]", "info")

    def _publish_log(self, message: str, level: str) -> None:
        log_message = {
            'service': 'api-gateway',
            'level': level,
            'message': message
        }
        self.rabbitmq_client.publish('logs', log_message)