import json
import threading
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.config.settings import ACTIVITY_EVENTS_QUEUE, LOG_SERVICE_QUEUE

class ActivityStateManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._activity_states = {}
        return cls._instance
    
    def set_paused(self, activity_uuid: str) -> None:
        self._activity_states[activity_uuid] = "pausada"
        print(f"[INFO] Actividad {activity_uuid} marcada como pausada")
    
    def set_active(self, activity_uuid: str) -> None:
        self._activity_states[activity_uuid] = "en_progreso"
        print(f"[INFO] Actividad {activity_uuid} marcada como activa")
    
    def set_completed(self, activity_uuid: str) -> None:
        self._activity_states[activity_uuid] = "completada"
        print(f"[INFO] Actividad {activity_uuid} marcada como completada")
    
    def set_abandoned(self, activity_uuid: str) -> None:
        self._activity_states[activity_uuid] = "abandonada"
        print(f"[INFO] Actividad {activity_uuid} marcada como abandonada")
    
    def is_paused(self, activity_uuid: str) -> bool:
        return self._activity_states.get(activity_uuid) == "pausada"
    
    def is_active(self, activity_uuid: str) -> bool:
        state = self._activity_states.get(activity_uuid)
        return state == "en_progreso" or state is None
    
    def remove(self, activity_uuid: str) -> None:
        if activity_uuid in self._activity_states:
            del self._activity_states[activity_uuid]
    
    def get_state(self, activity_uuid: str) -> str:
        return self._activity_states.get(activity_uuid, "unknown")


class ActivityEventConsumer:
    def __init__(self):
        self.rabbitmq_client = RabbitMQClient()
        self.state_manager = ActivityStateManager()

    def start(self) -> None:
        thread = threading.Thread(target=self._consume_events, daemon=True)
        thread.start()

    def _consume_events(self) -> None:
        self.rabbitmq_client.consume(ACTIVITY_EVENTS_QUEUE, self._callback)

    def _callback(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body)
            event_type = message.get("type")
            activity_uuid = message.get("activity_uuid")

            if not activity_uuid:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            if event_type == "activity_created":
                self.state_manager.set_active(activity_uuid)
            elif event_type == "activity_paused":
                self.state_manager.set_paused(activity_uuid)
            elif event_type == "activity_resumed":
                self.state_manager.set_active(activity_uuid)
            elif event_type == "activity_completed":
                self.state_manager.set_completed(activity_uuid)
            elif event_type == "activity_abandoned":
                self.state_manager.set_abandoned(activity_uuid)

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self._log(f"Error procesando evento de actividad: {str(e)}", "error")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _log(self, message: str, level: str = "info") -> None:
        log_message = {
            "service": "monitoring-service",
            "level": level,
            "message": message
        }
        self.rabbitmq_client.publish(LOG_SERVICE_QUEUE, log_message)