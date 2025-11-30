from typing import Dict
from fastapi import WebSocket
from src.infrastructure.ml.sequence_buffer import SequenceBuffer
from src.domain.services.intervention_controller import SessionContext

class ConnectionState:
    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.buffer = SequenceBuffer()
        self.context = SessionContext()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, ConnectionState] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> ConnectionState:
        await websocket.accept()
        state = ConnectionState(websocket, session_id)
        self.active_connections[session_id] = state
        print(f"[INFO] WebSocket conectado: sesion {session_id}")
        return state

    def disconnect(self, session_id: str) -> None:
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"[INFO] WebSocket desconectado: sesion {session_id}")

    def get_state(self, session_id: str) -> ConnectionState:
        return self.active_connections.get(session_id)

    def get_all_sessions(self) -> Dict[str, ConnectionState]:
        return self.active_connections

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)