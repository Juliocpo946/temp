import json
import uuid
import threading
from typing import Optional, Dict, Any, List, Callable
from upstash_redis import Redis
from src.infrastructure.config.settings import REDIS_URL, REDIS_TOKEN


class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.client = None
        self.instance_id = str(uuid.uuid4())[:8]
        self._pubsub_thread = None
        self._pubsub_running = False
        self._subscribers: Dict[str, List[Callable]] = {}
        if REDIS_URL and REDIS_TOKEN:
            try:
                self.client = Redis(url=REDIS_URL, token=REDIS_TOKEN)
                print(f"[REDIS_CLIENT] [INFO] Conectado a Redis - Instance ID: {self.instance_id}")
            except Exception as e:
                print(f"[REDIS_CLIENT] [ERROR] Error conectando a Redis: {str(e)}")
                self.client = None
        self._initialized = True

    def _is_available(self) -> bool:
        return self.client is not None

    def get_instance_id(self) -> str:
        return self.instance_id

    def register_connection(self, session_id: str, activity_uuid: str) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"ws_connection:{session_id}:{activity_uuid}"
            data = {
                "instance_id": self.instance_id,
                "activity_uuid": activity_uuid,
                "session_id": session_id
            }
            self.client.setex(key, 3600, json.dumps(data))

            session_key = f"ws_session_connections:{session_id}"
            existing = self.client.get(session_key)
            connections = json.loads(existing) if existing else []
            if activity_uuid not in connections:
                connections.append(activity_uuid)
            self.client.setex(session_key, 3600, json.dumps(connections))

            instance_key = f"ws_instance_sessions:{self.instance_id}"
            existing_sessions = self.client.get(instance_key)
            sessions = json.loads(existing_sessions) if existing_sessions else []
            if session_id not in sessions:
                sessions.append(session_id)
            self.client.setex(instance_key, 3600, json.dumps(sessions))

            print(f"[REDIS_CLIENT] [INFO] Conexion registrada: session={session_id}, activity={activity_uuid}, instance={self.instance_id}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error registrando conexion: {str(e)}")
            return False

    def unregister_connection(self, session_id: str, activity_uuid: str) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"ws_connection:{session_id}:{activity_uuid}"
            self.client.delete(key)

            session_key = f"ws_session_connections:{session_id}"
            existing = self.client.get(session_key)
            if existing:
                connections = json.loads(existing)
                if activity_uuid in connections:
                    connections.remove(activity_uuid)
                if connections:
                    self.client.setex(session_key, 3600, json.dumps(connections))
                else:
                    self.client.delete(session_key)

            print(f"[REDIS_CLIENT] [INFO] Conexion eliminada: session={session_id}, activity={activity_uuid}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error eliminando conexion: {str(e)}")
            return False

    def get_connection_instance(self, session_id: str, activity_uuid: str) -> Optional[Dict[str, Any]]:
        if not self._is_available():
            return None
        try:
            key = f"ws_connection:{session_id}:{activity_uuid}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo conexion: {str(e)}")
            return None

    def save_cooldown_state(self, session_id: str, activity_uuid: str, cooldown_data: Dict[str, Any]) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"cooldown_state:{session_id}:{activity_uuid}"
            self.client.setex(key, 3600, json.dumps(cooldown_data))
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error guardando cooldown: {str(e)}")
            return False

    def get_cooldown_state(self, session_id: str, activity_uuid: str) -> Optional[Dict[str, Any]]:
        if not self._is_available():
            return None
        try:
            key = f"cooldown_state:{session_id}:{activity_uuid}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo cooldown: {str(e)}")
            return None

    def track_websocket_metric(self, metric_type: str, activity_uuid: str) -> None:
        if not self._is_available():
            return
        try:
            key = f"ws_metric:{self.instance_id}:{metric_type}"
            self.client.incr(key)
            self.client.expire(key, 3600)
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error tracking metric: {str(e)}")

    def get_websocket_metrics(self) -> Dict[str, int]:
        if not self._is_available():
            return {}
        try:
            metrics = {}
            for metric_type in ["sent", "failed", "dropped"]:
                key = f"ws_metric:{self.instance_id}:{metric_type}"
                value = self.client.get(key)
                metrics[metric_type] = int(value) if value else 0
            return metrics
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo metricas: {str(e)}")
            return {}

    def close(self):
        self._pubsub_running = False