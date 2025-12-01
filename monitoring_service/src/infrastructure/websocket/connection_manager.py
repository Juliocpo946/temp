from typing import Dict, Optional, List
from dataclasses import dataclass
from fastapi import WebSocket
from src.infrastructure.ml.sequence_buffer import SequenceBuffer
from src.domain.services.intervention_controller import SessionContext
from src.infrastructure.cache.redis_client import RedisClient


@dataclass
class ActivityMetadata:
    user_id: int
    external_activity_id: int
    company_id: Optional[str] = None


class ConnectionState:
    def __init__(self, websocket: WebSocket, session_id: str, activity_uuid: str):
        self.websocket = websocket
        self.session_id = session_id
        self.activity_uuid = activity_uuid
        self.buffer = SequenceBuffer()
        self.context = SessionContext()
        self.metadata: Optional[ActivityMetadata] = None
        self.is_ready = False
        self._redis_client: Optional[RedisClient] = None

    def set_redis_client(self, redis_client: RedisClient) -> None:
        self._redis_client = redis_client
        self.context.set_redis_client(redis_client, self.session_id, self.activity_uuid)
        self.context.load_from_redis()

    def set_metadata(self, user_id: int, external_activity_id: int, company_id: Optional[str] = None) -> None:
        self.metadata = ActivityMetadata(
            user_id=user_id,
            external_activity_id=external_activity_id,
            company_id=company_id
        )
        self.is_ready = True
        self.context.reset_for_activity(external_activity_id)


class ConnectionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active_connections: Dict[str, ConnectionState] = {}
            cls._instance.redis_client = RedisClient()
        return cls._instance

    async def connect(self, websocket: WebSocket, session_id: str, activity_uuid: str) -> ConnectionState:
        await websocket.accept()
        state = ConnectionState(websocket, session_id, activity_uuid)
        state.set_redis_client(self.redis_client)
        self.active_connections[activity_uuid] = state
        
        self.redis_client.register_connection(session_id, activity_uuid)
        
        print(f"[INFO] WebSocket conectado: actividad {activity_uuid} (sesion {session_id})")
        return state

    def disconnect(self, activity_uuid: str) -> Optional[ConnectionState]:
        if activity_uuid in self.active_connections:
            state = self.active_connections[activity_uuid]
            
            state.context.save_to_redis()
            self.redis_client.unregister_connection(state.session_id, activity_uuid)
            
            del self.active_connections[activity_uuid]
            print(f"[INFO] WebSocket desconectado: actividad {activity_uuid}")
            return state
        return None

    def get_state(self, activity_uuid: str) -> Optional[ConnectionState]:
        return self.active_connections.get(activity_uuid)

    def get_state_by_session_id(self, session_id: str) -> Optional[ConnectionState]:
        for state in self.active_connections.values():
            if state.session_id == session_id:
                return state
        return None

    def get_all_states_by_session_id(self, session_id: str) -> List[ConnectionState]:
        return [
            state for state in self.active_connections.values()
            if state.session_id == session_id
        ]

    def get_all_connections(self) -> Dict[str, ConnectionState]:
        return self.active_connections

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)