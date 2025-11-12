import json
from fastapi import WebSocket
from src.infrastructure.http.http_client import HTTPClient
from src.infrastructure.config.settings import SESSION_SERVICE_URL

class VideoHandler:
    def __init__(self):
        self.http_client = HTTPClient()

    async def validate_session(self, session_id: str) -> bool:
        url = f"{SESSION_SERVICE_URL}/sessions/{session_id}"
        result = await self.http_client.get(url)
        if result and result.get('status') in ['activa', 'pausada']:
            return True
        return False

    async def handle_connection(self, websocket: WebSocket, session_id: str):
        await websocket.accept()

        is_valid = await self.validate_session(session_id)
        if not is_valid:
            await websocket.close(code=4000, reason="Invalid session")
            return

        analysis_active = True

        try:
            while True:
                message = await websocket.receive()

                if 'text' in message:
                    data = json.loads(message['text'])
                    tipo = data.get('tipo')

                    if tipo == 'video_chunk':
                        video_data = await websocket.receive_bytes()
                        if analysis_active:
                            await self.process_video_chunk(session_id, video_data)

                    elif tipo == 'pausar_analisis':
                        analysis_active = False
                        await websocket.send_json({'estado': 'analisis_pausado'})

                    elif tipo == 'reanudar_analisis':
                        analysis_active = True
                        await websocket.send_json({'estado': 'analisis_activo'})

                    elif tipo == 'video_frame':
                        if analysis_active:
                            await self.process_video_frame(session_id, data)

        except Exception as e:
            pass
        finally:
            await self.http_client.close()

    async def process_video_chunk(self, session_id: str, video_bytes: bytes):
        pass

    async def process_video_frame(self, session_id: str, data: dict):
        pass