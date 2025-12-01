import json
import threading
from typing import Dict, Any, List
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import INTERVENTION_EVALUATIONS_QUEUE, LOG_SERVICE_QUEUE


class InterventionEvaluationConsumer:
    def __init__(self, rabbitmq_client: RabbitMQClient, redis_client: RedisClient):
        self.rabbitmq_client = rabbitmq_client
        self.redis_client = redis_client
        self._negative_evaluations: Dict[str, int] = {}

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_evaluations, daemon=True)
        thread.start()
        print(f"[INTERVENTION_EVAL_CONSUMER] [INFO] Consumer de evaluaciones iniciado")

    def _consume_evaluations(self) -> None:
        try:
            self.rabbitmq_client.consume(INTERVENTION_EVALUATIONS_QUEUE, self._callback, with_dlq=True)
        except Exception as e:
            print(f"[INTERVENTION_EVAL_CONSUMER] [ERROR] Error en consumer: {str(e)}")

    def _callback(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            
            intervention_id = message.get("intervention_id")
            session_id = message.get("session_id")
            cognitive_event = message.get("cognitive_event")
            result = message.get("result")
            topic = message.get("topic")
            content_type = message.get("content_type")

            evaluation_data = {
                "intervention_id": intervention_id,
                "session_id": session_id,
                "cognitive_event": cognitive_event,
                "result": result,
                "topic": topic,
                "content_type": content_type
            }

            self.redis_client.store_intervention_evaluation(intervention_id, evaluation_data)

            if result in ["negative", "sin_efecto"]:
                self._track_negative_evaluation(topic, cognitive_event, content_type)

            print(f"[INTERVENTION_EVAL_CONSUMER] [INFO] Evaluacion procesada: {intervention_id} -> {result}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[INTERVENTION_EVAL_CONSUMER] [ERROR] Error procesando evaluacion: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _track_negative_evaluation(self, topic: str, cognitive_event: str, content_type: str) -> None:
        key = f"{topic}:{cognitive_event}:{content_type}"
        self._negative_evaluations[key] = self._negative_evaluations.get(key, 0) + 1
        
        if self._negative_evaluations[key] >= 3:
            print(f"[INTERVENTION_EVAL_CONSUMER] [WARNING] Contenido con evaluaciones negativas recurrentes: {key}")

    def get_content_effectiveness(self, topic: str, cognitive_event: str) -> Dict[str, Any]:
        evaluations = self.redis_client.get_intervention_evaluations_for_topic(topic)
        
        total = len(evaluations)
        if total == 0:
            return {"effectiveness": 0.5, "sample_size": 0}
        
        positive = sum(1 for e in evaluations if e.get("result") == "positive")
        negative = sum(1 for e in evaluations if e.get("result") in ["negative", "sin_efecto"])
        
        effectiveness = positive / total if total > 0 else 0.5
        
        return {
            "effectiveness": effectiveness,
            "positive": positive,
            "negative": negative,
            "sample_size": total
        }

    def should_avoid_content_type(self, topic: str, cognitive_event: str, content_type: str) -> bool:
        key = f"{topic}:{cognitive_event}:{content_type}"
        return self._negative_evaluations.get(key, 0) >= 3

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "recommendation-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)