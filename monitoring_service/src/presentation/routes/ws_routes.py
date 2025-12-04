import json
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.websocket.connection_manager import manager
from src.infrastructure.websocket.frame_handler import FrameHandler
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.websocket_event_publisher import WebsocketEventPublisher

router = APIRouter()
rabbitmq_client = RabbitMQClient()
websocket_publisher = WebsocketEventPublisher(rabbitmq_client)


@router.websocket("/ws/{session_id}/{activity_uuid}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, activity_uuid: str):
    state = await manager.connect(websocket, session_id, activity_uuid)
    db = SessionLocal()

    try:
        handler = FrameHandler(db, rabbitmq_client)

        while True:
            raw_message = await websocket.receive_text()
            result = await handler.handle(state, raw_message)

            if result:
                await websocket.send_text(json.dumps(result))

    except WebSocketDisconnect:
        disconnected_state = manager.disconnect(activity_uuid)
        if disconnected_state:
            websocket_publisher.publish_websocket_disconnected(
                activity_uuid=activity_uuid,
                session_id=session_id,
                reason="client_disconnected"
            )
    except Exception as e:
        print(f"[WS_ROUTES] [ERROR] Error en WebSocket {activity_uuid}: {e}")
        print(f"[WS_ROUTES] [ERROR] Traceback completo:")
        traceback.print_exc()
        disconnected_state = manager.disconnect(activity_uuid)
        if disconnected_state:
            websocket_publisher.publish_websocket_disconnected(
                activity_uuid=activity_uuid,
                session_id=session_id,
                reason=f"error: {str(e)}"
            )
    finally:
        db.close()


@router.get("/ws/connections")
def get_connections():
    connections = manager.get_all_connections()
    return {
        "active_connections": manager.connection_count,
        "activities": [
            {
                "activity_uuid": activity_uuid,
                "session_id": state.session_id,
                "is_ready": state.is_ready,
                "user_id": state.metadata.user_id if state.metadata else None,
                "external_activity_id": state.metadata.external_activity_id if state.metadata else None
            }
            for activity_uuid, state in connections.items()
        ]
    }