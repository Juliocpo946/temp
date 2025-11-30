import json
import threading
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import MONITORING_EVENTS_QUEUE, RECOMMENDATIONS_QUEUE
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.content_repository_impl import ContentRepositoryImpl
from src.infrastructure.http.session_client import SessionClient
from src.infrastructure.http.gemini_client import GeminiClient
from src.application.use_cases.process_intervention import ProcessInterventionUseCase
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO


class InterventionConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.session_client = SessionClient()
        self.gemini_client = GeminiClient()

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_events, daemon=True)
        thread.start()

    def _consume_events(self) -> None:
        self.rabbitmq_client.consume(MONITORING_EVENTS_QUEUE, self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        db = SessionLocal()
        try:
            message = json.loads(body)
            event = MonitoringEventDTO.from_dict(message)

            content_repository = ContentRepositoryImpl(db)
            use_case = ProcessInterventionUseCase(
                content_repository=content_repository,
                session_client=self.session_client,
                gemini_client=self.gemini_client
            )

            recommendation = use_case.execute(event)

            if recommendation:
                queue_name = f"{RECOMMENDATIONS_QUEUE}.session.{event.session_id}"
                self.rabbitmq_client.publish(queue_name, recommendation)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    def close(self) -> None:
        self.rabbitmq_client.close()