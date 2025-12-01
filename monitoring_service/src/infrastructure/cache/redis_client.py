import json
import uuid
from typing import Optional, Dict, Any, List
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

    def get_all_connections_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        if not self._is_available():
            return []
        try:
            session_key = f"ws_session_connections:{session_id}"
            existing = self.client.get(session_key)
            if not existing:
                return []

            connections = json.loads(existing)
            result = []
            for activity_uuid in connections:
                conn_data = self.get_connection_instance(session_id, activity_uuid)
                if conn_data:
                    result.append(conn_data)
            return result
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo conexiones de sesion: {str(e)}")
            return []

    def publish_recommendation(self, session_id: str, recommendation: Dict[str, Any]) -> bool:
        if not self._is_available():
            return False
        try:
            channel = f"recommendations:{session_id}"
            self.client.publish(channel, json.dumps(recommendation))
            print(f"[REDIS_CLIENT] [INFO] Recomendacion publicada en canal: {channel}")
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error publicando recomendacion: {str(e)}")
            return False

    def save_cooldown_state(self, session_id: str, activity_uuid: str, cooldown_data: Dict[str, Any]) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"cooldown_state:{session_id}:{activity_uuid}"
            self.client.setex(key, 3600, json.dumps(cooldown_data))
            print(f"[REDIS_CLIENT] [INFO] Estado de cooldown guardado: session={session_id}, activity={activity_uuid}")
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
                print(f"[REDIS_CLIENT] [INFO] Estado de cooldown recuperado: session={session_id}, activity={activity_uuid}")
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo cooldown: {str(e)}")
            return None

    def delete_cooldown_state(self, session_id: str, activity_uuid: str) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"cooldown_state:{session_id}:{activity_uuid}"
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error eliminando cooldown: {str(e)}")
            return False

    def set_health_status(self, component: str, status: Dict[str, Any]) -> bool:
        if not self._is_available():
            return False
        try:
            key = f"health:{self.instance_id}:{component}"
            self.client.setex(key, 60, json.dumps(status))
            return True
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error guardando health status: {str(e)}")
            return False

    def get_health_status(self, component: str) -> Optional[Dict[str, Any]]:
        if not self._is_available():
            return None
        try:
            key = f"health:{self.instance_id}:{component}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[REDIS_CLIENT] [ERROR] Error obteniendo health status: {str(e)}")
            return None

    def close(self):
        pass