import pika
from typing import List, Dict, Any, Tuple
from src.infrastructure.config.settings import AMQP_URL


class QueueValidator:
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self) -> bool:
        try:
            parameters = pika.URLParameters(AMQP_URL)
            parameters.socket_timeout = 10
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            return True
        except Exception as e:
            print(f"[QUEUE_VALIDATOR] [ERROR] Error conectando a RabbitMQ: {str(e)}")
            return False

    def close(self) -> None:
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception:
            pass

    def validate_queue_exists(self, queue_name: str) -> Tuple[bool, Dict[str, Any]]:
        try:
            result = self.channel.queue_declare(queue=queue_name, passive=True)
            return True, {
                "queue": queue_name,
                "message_count": result.method.message_count,
                "consumer_count": result.method.consumer_count
            }
        except pika.exceptions.ChannelClosedByBroker:
            self.channel = self.connection.channel()
            return False, {"queue": queue_name, "error": "Cola no existe"}
        except Exception as e:
            return False, {"queue": queue_name, "error": str(e)}

    def validate_queue_has_consumers(self, queue_name: str, min_consumers: int = 0) -> Tuple[bool, Dict[str, Any]]:
        exists, info = self.validate_queue_exists(queue_name)
        if not exists:
            return False, info

        consumer_count = info.get("consumer_count", 0)
        has_consumers = consumer_count >= min_consumers

        return has_consumers, {
            "queue": queue_name,
            "consumer_count": consumer_count,
            "min_required": min_consumers,
            "status": "ok" if has_consumers else "warning"
        }

    def validate_queues(self, queue_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = {
            "all_exist": True,
            "all_have_consumers": True,
            "queues": [],
            "warnings": [],
            "errors": []
        }

        for config in queue_configs:
            queue_name = config.get("name")
            require_consumers = config.get("require_consumers", False)
            min_consumers = config.get("min_consumers", 1)

            exists, info = self.validate_queue_exists(queue_name)

            queue_result = {
                "name": queue_name,
                "exists": exists,
                "consumer_count": info.get("consumer_count", 0),
                "message_count": info.get("message_count", 0)
            }

            if not exists:
                results["all_exist"] = False
                results["errors"].append(f"Cola no existe: {queue_name}")
                queue_result["status"] = "error"
            elif require_consumers:
                has_consumers, consumer_info = self.validate_queue_has_consumers(queue_name, min_consumers)
                if not has_consumers:
                    results["all_have_consumers"] = False
                    results["warnings"].append(
                        f"Cola {queue_name} tiene {consumer_info['consumer_count']} consumers (minimo requerido: {min_consumers})"
                    )
                    queue_result["status"] = "warning"
                else:
                    queue_result["status"] = "ok"
            else:
                queue_result["status"] = "ok"

            results["queues"].append(queue_result)

        return results

    def create_queue_if_not_exists(self, queue_name: str, with_dlq: bool = True) -> bool:
        try:
            if with_dlq:
                dlq_name = f"{queue_name}_dlq"
                self.channel.queue_declare(queue=dlq_name, durable=True)
                self.channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    arguments={
                        'x-dead-letter-exchange': '',
                        'x-dead-letter-routing-key': dlq_name
                    }
                )
            else:
                self.channel.queue_declare(queue=queue_name, durable=True)
            return True
        except Exception as e:
            print(f"[QUEUE_VALIDATOR] [ERROR] Error creando cola {queue_name}: {str(e)}")
            return False


def validate_service_queues(required_queues: List[Dict[str, Any]], create_missing: bool = True) -> Tuple[bool, Dict[str, Any]]:
    validator = QueueValidator()

    if not validator.connect():
        return False, {"error": "No se pudo conectar a RabbitMQ"}

    try:
        results = validator.validate_queues(required_queues)

        if create_missing and not results["all_exist"]:
            print(f"[QUEUE_VALIDATOR] [INFO] Creando colas faltantes...")
            for queue_info in results["queues"]:
                if not queue_info["exists"]:
                    queue_name = queue_info["name"]
                    config = next((q for q in required_queues if q["name"] == queue_name), {})
                    with_dlq = config.get("with_dlq", True)

                    if validator.create_queue_if_not_exists(queue_name, with_dlq):
                        print(f"[QUEUE_VALIDATOR] [INFO] Cola creada: {queue_name}")
                        queue_info["exists"] = True
                        queue_info["status"] = "created"
                    else:
                        print(f"[QUEUE_VALIDATOR] [ERROR] No se pudo crear cola: {queue_name}")

            results["all_exist"] = all(q["exists"] for q in results["queues"])

        is_valid = results["all_exist"]

        if results["warnings"]:
            for warning in results["warnings"]:
                print(f"[QUEUE_VALIDATOR] [WARNING] {warning}")

        if results["errors"]:
            for error in results["errors"]:
                print(f"[QUEUE_VALIDATOR] [ERROR] {error}")

        return is_valid, results

    finally:
        validator.close()