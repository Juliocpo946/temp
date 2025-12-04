import json
import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from fastapi import WebSocket
from src.infrastructure.ml.feature_buffer import FeatureBuffer
from src.infrastructure.ml.temporal_feature_extractor import TemporalFeatureExtractor
from src.infrastructure.ml.cognitive_state_detector import CognitiveStateDetector
from src.domain.services.intervention_controller import SessionContext
from src.infrastructure.cache.redis_client import RedisClient


@dataclass
class ActivityMetadata:
    user_id: int
    external_activity_id: int
    company_id: Optional[str] = None


@dataclass
class BackpressureMetrics:
    frames_received: int = 0
    frames_processed: int = 0
    frames_dropped: int = 0
    throttle_events: int = 0
    last_throttle_at: Optional[datetime] = None
    is_throttled: bool = False
    throttle_until: Optional[datetime] = None


class ConnectionState:
    MAX_BUFFER_SIZE = 300
    THROTTLE_THRESHOLD = 250
    THROTTLE_DURATION_SECONDS = 2
    MAX_FRAMES_PER_SECOND = 60

    def __init__(self, websocket: WebSocket, session_id: str, activity_uuid: str):
        self.websocket = websocket
        self.session_id = session_id
        self.activity_uuid = activity_uuid
        
        self.feature_buffer = FeatureBuffer()
        self.feature_extractor = TemporalFeatureExtractor()
        self.state_detector = CognitiveStateDetector()
        self.context = SessionContext()
        
        self.metadata: Optional[ActivityMetadata] = None
        self.is_ready = False
        self._redis_client: Optional[RedisClient] = None
        
        self._frame_buffer: List[Dict] = []
        self._backpressure = BackpressureMetrics()
        self._frame_timestamps: List[datetime] = []
        self._last_frame_time: Optional[datetime] = None

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

    def can_accept_frame(self) -> bool:
        now = datetime.utcnow()
        
        if self._backpressure.is_throttled:
            if self._backpressure.throttle_until and now >= self._backpressure.throttle_until:
                self._backpressure.is_throttled = False
                self._backpressure.throttle_until = None
                print(f"[BACKPRESSURE] [INFO] Throttle terminado para actividad: {self.activity_uuid}")
            else:
                return False

        if len(self._frame_buffer) >= self.MAX_BUFFER_SIZE:
            self._backpressure.frames_dropped += 1
            self._track_dropped_frame()
            return False

        cutoff_time = datetime.utcnow()
        self._frame_timestamps = [
            ts for ts in self._frame_timestamps 
            if (cutoff_time - ts).total_seconds() < 1.0
        ]

        if len(self._frame_timestamps) >= self.MAX_FRAMES_PER_SECOND:
            self._backpressure.frames_dropped += 1
            self._track_dropped_frame()
            return False

        if len(self._frame_buffer) >= self.THROTTLE_THRESHOLD:
            self._activate_throttle()
            return False

        return True

    def add_frame_to_buffer(self, frame: Dict) -> bool:
        if not self.can_accept_frame():
            return False

        self._frame_buffer.append(frame)
        self._frame_timestamps.append(datetime.utcnow())
        self._backpressure.frames_received += 1
        self._last_frame_time = datetime.utcnow()
        return True

    def get_next_frame(self) -> Optional[Dict]:
        if self._frame_buffer:
            frame = self._frame_buffer.pop(0)
            self._backpressure.frames_processed += 1
            return frame
        return None

    def get_buffer_size(self) -> int:
        return len(self._frame_buffer)

    def get_buffer_utilization(self) -> float:
        return len(self._frame_buffer) / self.MAX_BUFFER_SIZE

    def _activate_throttle(self) -> None:
        now = datetime.utcnow()
        self._backpressure.is_throttled = True
        self._backpressure.throttle_events += 1
        self._backpressure.last_throttle_at = now
        self._backpressure.throttle_until = now + timedelta(seconds=self.THROTTLE_DURATION_SECONDS)
        
        print(f"[BACKPRESSURE] [WARNING] Throttle activado para actividad: {self.activity_uuid}, buffer: {len(self._frame_buffer)}")
        self._track_throttle_event()

    def _track_dropped_frame(self) -> None:
        if self._redis_client:
            self._redis_client.track_websocket_metric("dropped", self.activity_uuid)

    def _track_throttle_event(self) -> None:
        if self._redis_client:
            self._redis_client.track_websocket_metric("throttled", self.activity_uuid)

    def get_backpressure_metrics(self) -> Dict:
        return {
            "frames_received": self._backpressure.frames_received,
            "frames_processed": self._backpressure.frames_processed,
            "frames_dropped": self._backpressure.frames_dropped,
            "throttle_events": self._backpressure.throttle_events,
            "is_throttled": self._backpressure.is_throttled,
            "buffer_size": len(self._frame_buffer),
            "buffer_utilization": self.get_buffer_utilization()
        }

    def get_throttle_message(self) -> Dict:
        return {
            "type": "throttle",
            "status": "active",
            "reason": "rate_limit_exceeded",
            "retry_after_seconds": self.THROTTLE_DURATION_SECONDS,
            "buffer_size": len(self._frame_buffer),
            "max_buffer_size": self.MAX_BUFFER_SIZE
        }

    async def send_personal_message(self, message: Dict, activity_uuid: str):
        try:
            text_message = json.dumps(message)
            await self.websocket.send_text(text_message)
            return True
        except Exception as e:
            print(f"[CONNECTION_STATE] [ERROR] Error enviando mensaje WS: {e}")
            return False


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

        print(f"[CONNECTION_MANAGER] [INFO] WebSocket conectado: actividad {activity_uuid} (sesion {session_id})")
        return state

    def disconnect(self, activity_uuid: str) -> Optional[ConnectionState]:
        if activity_uuid in self.active_connections:
            state = self.active_connections[activity_uuid]

            metrics = state.get_backpressure_metrics()
            if metrics["frames_dropped"] > 0:
                print(f"[BACKPRESSURE] [INFO] Metricas finales para {activity_uuid}: dropped={metrics['frames_dropped']}, throttles={metrics['throttle_events']}")

            state.context.save_to_redis()
            self.redis_client.unregister_connection(state.session_id, activity_uuid)

            del self.active_connections[activity_uuid]
            print(f"[CONNECTION_MANAGER] [INFO] WebSocket desconectado: actividad {activity_uuid}")
            return state
        return None

    def get_state(self, activity_uuid: str) -> Optional[ConnectionState]:
        return self.active_connections.get(activity_uuid)
        
    def has_connection(self, activity_uuid: str) -> bool:
        return activity_uuid in self.active_connections

    async def send_personal_message(self, message: Dict, activity_uuid: str):
        if activity_uuid in self.active_connections:
            state = self.active_connections[activity_uuid]
            return await state.send_personal_message(message, activity_uuid)
        return False

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

    def get_all_backpressure_metrics(self) -> Dict[str, Dict]:
        return {
            activity_uuid: state.get_backpressure_metrics()
            for activity_uuid, state in self.active_connections.items()
        }

    def get_problematic_connections(self, drop_threshold: int = 10) -> List[str]:
        problematic = []
        for activity_uuid, state in self.active_connections.items():
            metrics = state.get_backpressure_metrics()
            if metrics["frames_dropped"] >= drop_threshold or metrics["is_throttled"]:
                problematic.append(activity_uuid)
        return problematic

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()