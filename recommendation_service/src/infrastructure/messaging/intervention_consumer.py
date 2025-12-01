import json
import threading
import pika
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.activity_details_client import ActivityDetailsClient
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import (
    MONITORING_EVENTS_QUEUE,
    RECOMMENDATIONS_QUEUE,
    LOG_SERVICE_QUEUE,
    AMQP_URL,
    INTERVENTION_CONSUMER_WORKERS,
    PREFETCH_COUNT
)
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.content_repository_impl import ContentRepositoryImpl
from src.infrastructure.http.gemini_client import GeminiClient
from src.application.use_cases.process_intervention import ProcessInterventionUseCase
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO


class InterventionConsumer:
    def __init__(self):
        self.redis_client = RedisClient()
        self.rabbitmq_client = RabbitMQClient()
        self.activity_details_client = ActivityDetailsClient(self.rabbitmq_client, self.redis_client)
        self.gemini_client = GeminiClient(self.redis_client)
        self.executor = ThreadPoolExecutor(max_workers=INTERVENTION_CONSUMER_WORKERS)
        self._running = False
        self._connection = None
        self._channel = None

    def start(self) -> None:
        self._running = True
        thread = threading.Thread(target=self._consume_events, daemon=True)
        thread.start()
        print(f"[INTERVENTION_CONSUMER] [INFO] Consumer iniciado con {INTERVENTION_CONSUMER_WORKERS} workers y prefetch={PREFETCH_COUNT}")

    def _consume_events(self) -> None:
        try:
            parameters = pika.URLParameters(AMQP_URL)
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()

            self._channel.queue_declare(queue=MONITORING_EVENTS_QUEUE, durable=True)
            self._channel.basic_qos(prefetch_count=PREFETCH_COUNT)

            self._channel.basic_consume(
                queue=MONITORING_EVENTS_QUEUE,
                on_message_callback=self._on_message,
                auto_ack=False
            )

            print(f"[INTERVENTION_CONSUMER] [INFO] Escuchando en cola: {MONITORING_EVENTS_QUEUE}")
            self._channel.start_consuming()

        except Exception as e:
            print(f"[INTERVENTION_CONSUMER] [ERROR] Error en consumer: {str(e)}")
            if self._running:
                threading.Timer(5.0, self._consume_events).start()

    def _on_message(self, ch, method, properties, body) -> None:
        self.executor.submit(self._process_message, ch, method, body)

    def _process_message(self, ch, method, body) -> None:
        db = SessionLocal()
        try:
            message = json.loads(body)
            event = MonitoringEventDTO.from_dict(message)

            print(f"[INTERVENTION_CONSUMER] [INFO] Procesando evento para sesion: {event.session_id}")

            content_repository = ContentRepositoryImpl(db)
            use_case = ProcessInterventionUseCase(
                content_repository=content_repository,
                activity_details_client=self.activity_details_client,
                gemini_client=self.gemini_client,
                redis_client=self.redis_client
            )

            recommendation = use_case.execute(event)

            if recommendation:
                success = self.rabbitmq_client.publish(RECOMMENDATIONS_QUEUE, recommendation)
                if success:
                    print(f"[INTERVENTION_CONSUMER] [INFO] Recomendacion publicada en cola: {RECOMMENDATIONS_QUEUE}")
                    self._log(f"Recomendacion publicada para sesion: {event.session_id}")
                else:
                    print(f"[INTERVENTION_CONSUMER] [ERROR] Error publicando recomendacion")
                    self._log(f"Error publicando recomendacion para sesion: {event.session_id}", "error")

            self._safe_ack(ch, method.delivery_tag)

        except Exception as e:
            print(f"[INTERVENTION_CONSUMER] [ERROR] Error procesando evento: {str(e)}")
            self._log(f"Error procesando evento: {str(e)}", "error")
            self._safe_nack(ch, method.delivery_tag)
        finally:
            db.close()

    def _safe_ack(self, ch, delivery_tag) -> None:
        try:
            if ch.is_open:
                ch.basic_ack(delivery_tag=delivery_tag)
        except Exception as e:
            print(f"[INTERVENTION_CONSUMER] [ERROR] Error en ack: {str(e)}")

    def _safe_nack(self, ch, delivery_tag) -> None:
        try:
            if ch.is_open:
                ch.basic_nack(delivery_tag=delivery_tag, requeue=True)
        except Exception as e:
            print(f"[INTERVENTION_CONSUMER] [ERROR] Error en nack: {str(e)}")

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "recommendation-service",
            "level": level,
            "message": message
        }
        try:
            self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)
        except Exception:
            pass

    def close(self) -> None:
        self._running = False
        self.executor.shutdown(wait=False)
        try:
            if self._channel and self._channel.is_open:
                self._channel.stop_consuming()
            if self._connection and self._connection.is_open:
                self._connection.close()
        except Exception as e:
            print(f"[INTERVENTION_CONSUMER] [ERROR] Error cerrando consumer: {str(e)}")
        self.rabbitmq_client.close()
        print(f"[INTERVENTION_CONSUMER] [INFO] Consumer de intervenciones cerrado")