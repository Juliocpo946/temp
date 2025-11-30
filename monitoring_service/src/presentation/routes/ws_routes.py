import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db, SessionLocal
from src.infrastructure.websocket.connection_manager import ConnectionManager
from src.infrastructure.websocket.frame_handler import FrameHandler

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    state = await manager.connect(websocket, session_id)
    db = SessionLocal()
    
    try:
        handler = FrameHandler(db)
        
        while True:
            raw_message = await websocket.receive_text()
            result = await handler.handle(state, raw_message)
            
            if result:
                await websocket.send_text(json.dumps(result))
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"[ERROR] Error en WebSocket {session_id}: {e}")
        manager.disconnect(session_id)
    finally:
        db.close()

@router.get("/ws/connections")
def get_connections():
    return {
        "active_connections": manager.connection_count,
        "sessions": list(manager.get_all_sessions().keys())
    }