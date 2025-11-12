from fastapi import APIRouter, WebSocket, Query
from src.infrastructure.websocket.video_handler import VideoHandler

router = APIRouter()

@router.websocket("/ws/cognitive")
async def websocket_endpoint(websocket: WebSocket, session_id: str = Query(...)):
    handler = VideoHandler()
    await handler.handle_connection(websocket, session_id)