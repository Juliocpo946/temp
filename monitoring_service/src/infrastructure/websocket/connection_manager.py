from typing import Dict, Optional
from fastapi import WebSocket
from src.infrastructure.ml.sequence_buffer import SequenceBuffer
from src.domain.services.intervention_controller import SessionContext

class ConnectionState:
    def __init__(self, websocket: WebSocket, session_id: str, activity_uuid: str):
        self.websocket = websocket
        self.session_id = session_id
        self.activity_uuid = activity_uuid
        self.buffer = SequenceBuffer()
        self.context = SessionContext()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, ConnectionState] = {}

    async def connect(self, websocket: WebSocket, session_id: str, activity_uuid: str) -> ConnectionState:
        await websocket.accept()
        state = ConnectionState(websocket, session_id, activity_uuid)
        self.active_connections[activity_uuid] = state
        print(f"[INFO] WebSocket conectado: actividad {activity_uuid} (sesion {session_id})")
        return state

    def disconnect(self, activity_uuid: str) -> Optional[ConnectionState]:
        if activity_uuid in self.active_connections:
            state = self.active_connections[activity_uuid]
            del self.active_connections[activity_uuid]
            print(f"[INFO] WebSocket desconectado: actividad {activity_uuid}")
            return state
        return None

    def get_state(self, activity_uuid: str) -> Optional[ConnectionState]:
        return self.active_connections.get(activity_uuid)

    def get_all_connections(self) -> Dict[str, ConnectionState]:
        return self.active_connections

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)