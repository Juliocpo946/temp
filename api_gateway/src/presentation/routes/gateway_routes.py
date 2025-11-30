import asyncio
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from src.infrastructure.config.settings import MONITORING_SERVICE_WS_URL, AUTH_SERVICE_URL
from src.infrastructure.http.http_client import HTTPClient
from src.infrastructure.cache.redis_client import RedisClient

router = APIRouter()
http_client = HTTPClient()
redis_client = RedisClient()

async def validate_api_key(api_key: str) -> dict:
    cached_data = redis_client.get_api_key(api_key)
    
    if cached_data:
        if not cached_data.get('is_active'):
            return {'valid': False, 'reason': 'API key inactiva'}
        return {
            'valid': True,
            'company_id': cached_data.get('company_id'),
            'application_id': cached_data.get('application_id')
        }
    
    try:
        validation_url = f"{AUTH_SERVICE_URL}/auth/api-keys/validate"
        response = await http_client.post(validation_url, json={"key_value": api_key})
        
        if response.get('valid'):
            cache_data = {
                'company_id': response['company_id'],
                'application_id': response.get('application_id'),
                'is_active': True
            }
            redis_client.set_api_key(api_key, cache_data, ttl=3600)
            return {
                'valid': True,
                'company_id': response['company_id'],
                'application_id': response.get('application_id')
            }
        return {'valid': False, 'reason': 'API key invalida'}
    except Exception as e:
        print(f"[GATEWAY WS] Error validando API key: {e}")
        return {'valid': False, 'reason': str(e)}

def build_monitoring_ws_url(session_id: str, activity_uuid: str) -> str:
    base_url = MONITORING_SERVICE_WS_URL
    if not base_url:
        base_url = "ws://localhost:3008"
    
    if base_url.startswith("http://"):
        base_url = base_url.replace("http://", "ws://")
    elif base_url.startswith("https://"):
        base_url = base_url.replace("https://", "wss://")
    elif not base_url.startswith("ws://") and not base_url.startswith("wss://"):
        base_url = f"ws://{base_url}"
    
    return f"{base_url}/ws/{session_id}/{activity_uuid}"

@router.websocket("/ws/{session_id}/{activity_uuid}")
async def websocket_proxy(websocket: WebSocket, session_id: str, activity_uuid: str):
    api_key = None
    
    auth_header = websocket.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        api_key = auth_header.split(" ")[1]
    
    if not api_key:
        api_key = websocket.query_params.get("api_key")
    
    if not api_key:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="API key requerida")
        return
    
    auth_result = await validate_api_key(api_key)
    if not auth_result['valid']:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=auth_result.get('reason', 'No autorizado'))
        return
    
    company_id = auth_result.get('company_id')
    
    await websocket.accept()
    print(f"[GATEWAY WS] Conexion aceptada: session={session_id}, activity={activity_uuid}, company={company_id}")
    
    monitoring_url = build_monitoring_ws_url(session_id, activity_uuid)
    
    try:
        async with websockets.connect(monitoring_url) as monitoring_ws:
            print(f"[GATEWAY WS] Conectado a Monitoring: {monitoring_url}")
            
            async def forward_to_monitoring():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await monitoring_ws.send(data)
                except WebSocketDisconnect:
                    print(f"[GATEWAY WS] Cliente desconectado: {activity_uuid}")
                except Exception as e:
                    print(f"[GATEWAY WS] Error recibiendo del cliente: {e}")
            
            async def forward_to_client():
                try:
                    async for message in monitoring_ws:
                        await websocket.send_text(message)
                except Exception as e:
                    print(f"[GATEWAY WS] Error recibiendo de Monitoring: {e}")
            
            await asyncio.gather(
                forward_to_monitoring(),
                forward_to_client(),
                return_exceptions=True
            )
            
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"[GATEWAY WS] Conexion con Monitoring cerrada: {e}")
    except Exception as e:
        print(f"[GATEWAY WS] Error conectando a Monitoring: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Error conectando al servicio de monitoreo")
    finally:
        try:
            await websocket.close()
        except:
            pass
        print(f"[GATEWAY WS] Conexion cerrada: {activity_uuid}")