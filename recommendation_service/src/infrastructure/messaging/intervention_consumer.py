import json
import threading
from datetime import datetime
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.activity_details_client import ActivityDetailsClient
from src.infrastructure.config.settings import MONITORING_EVENTS_QUEUE, RECOMMENDATIONS_QUEUE
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.content_repository_impl import ContentRepositoryImpl
from src.infrastructure.http.gemini_client import GeminiClient
from src.application.use_cases.process_intervention import ProcessInterventionUseCase
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO


class InterventionConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.activity_details_client = ActivityDetailsClient(self.rabbitmq_client)
        self.gemini_client = GeminiClient()

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_events, daemon=True)
        thread.start()
        print(f"[INTERVENTION_CONSUMER] [INFO] Consumer de intervenciones iniciado")

    def _consume_events(self) -> None:
        self.rabbitmq_client.consume(MONITORING_EVENTS_QUEUE, self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        db = SessionLocal()
        try:
            message = json.loads(body)
            event = MonitoringEventDTO.from_dict(message)

            print(f"[INTERVENTION_CONSUMER] [INFO] Evento recibido para sesion: {event.session_id}")

            content_repository = ContentRepositoryImpl(db)
            use_case = ProcessInterventionUseCase(
                content_repository=content_repository,
                activity_details_client=self.activity_details_client,
                gemini_client=self.gemini_client
            )

            recommendation = use_case.execute(event)

            if recommendation:
                queue_name = f"{RECOMMENDATIONS_QUEUE}.session.{event.session_id}"
                success = self.rabbitmq_client.publish(queue_name, recommendation)
                if success:
                    print(f"[INTERVENTION_CONSUMER] [INFO] Recomendacion publicada en cola: {queue_name}")
                else:
                    print(f"[INTERVENTION_CONSUMER] [ERROR] Error publicando recomendacion en cola: {queue_name}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[INTERVENTION_CONSUMER] [ERROR] Error procesando evento: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    def close(self) -> None:
        self.rabbitmq_client.close()
        print(f"[INTERVENTION_CONSUMER] [INFO] Consumer de intervenciones cerrado")