import json
import threading
from datetime import datetime
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import MONITORING_EVENTS_QUEUE, RECOMMENDATIONS_QUEUE
from src.application.use_cases.generate_recommendation import GenerateRecommendationUseCase
from src.application.dtos.monitoring_event_dto import MonitoringEventDTO

class RecommendationConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.generate_recommendation_use_case = GenerateRecommendationUseCase()

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_events, daemon=True)
        thread.start()

    def _consume_events(self) -> None:
        self.rabbitmq_client.consume(MONITORING_EVENTS_QUEUE, self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            event = MonitoringEventDTO.from_dict(message)
            
            recommendation = self.generate_recommendation_use_case.execute(event)
            
            if recommendation and recommendation.get('accion') != 'nada':
                self.rabbitmq_client.publish(RECOMMENDATIONS_QUEUE, recommendation)
                print(f"[INFO] Recomendación enviada: {recommendation.get('accion')}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"[ERROR] Error procesando evento de monitoreo: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)