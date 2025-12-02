import json
import threading
import pika
from typing import Dict
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import (
    INTERVENTION_EVALUATIONS_QUEUE,
    LOG_SERVICE_QUEUE,
    AMQP_URL
)


class InterventionEvaluationConsumer:
    def __init__(self, rabbitmq_client, redis_client: RedisClient):
        self.rabbitmq_client = rabbitmq_client
        self.redis_client = redis_client
        self._negative_evaluations: Dict[str, int] = {}
        self._connection = None
        self._channel = None

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_evaluations, daemon=True)
        thread.start()
        print(f"[INTERVENTION_EVAL_CONSUMER] [INFO] Consumer de evaluaciones iniciado")

    def _consume_evaluations(self) -> None:
        while True:
            try:
                parameters = pika.URLParameters(AMQP_URL)
                parameters.heartbeat = 300
                parameters.blocked_connection_timeout = 150
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                
                self._channel.basic_qos(prefetch_count=10)
                self._channel.basic_consume(
                    queue=INTERVENTION_EVALUATIONS_QUEUE,
                    on_message_callback=self._callback,
                    auto_ack=False
                )
                
                print(f"[INTERVENTION_EVAL_CONSUMER] [INFO] Escuchando en cola: {INTERVENTION_EVALUATIONS_QUEUE}")
                self._channel.start_consuming()
            except Exception as e:
                print(f"[INTERVENTION_EVAL_CONSUMER] [ERROR] Error en consumer: {str(e)}")
                import time
                time.sleep(5)

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
            print(f"[INTERVENTION_EVAL_CONSUMER] [WARNING] Contenido con multiples evaluaciones negativas: {key}")