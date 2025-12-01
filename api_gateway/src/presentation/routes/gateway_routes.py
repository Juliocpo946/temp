import asyncio
from typing import Optional, Dict, Any
from collections import deque
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, status, Response
from fastapi.responses import JSONResponse
import websockets
import httpx
from src.infrastructure.config.settings import (
    AUTH_SERVICE_URL,
    SESSION_SERVICE_URL,
    RECOMMENDATION_SERVICE_URL,
    MONITORING_SERVICE_URL,
    MONITORING_SERVICE_WS_URL,
    LOG_SERVICE_URL
)

router = APIRouter()

http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)


SERVICE_ROUTES = {
    "/auth": AUTH_SERVICE_URL,
    "/sessions": SESSION_SERVICE_URL,
    "/activities": SESSION_SERVICE_URL,
    "/contents": RECOMMENDATION_SERVICE_URL,
    "/recommendations": RECOMMENDATION_SERVICE_URL,
    "/monitoring": MONITORING_SERVICE_URL,
    "/logs": LOG_SERVICE_URL,
}


class WebSocketProxyState:
    def __init__(self, max_buffer_size: int = 100):
        self.pending_messages: deque = deque(maxlen=max_buffer_size)
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 1.0


def get_target_service(path: str) -> Optional[str]:
    for prefix, service_url in SERVICE_ROUTES.items():
        if path.startswith(prefix):
            return service_url
    return None


async def proxy_request(
    request: Request,
    target_url: str,
    path: str
) -> Response:
    headers = dict(request.headers)
    headers.pop("host", None)

    if hasattr(request.state, "company_id") and request.state.company_id:
        headers["X-Company-ID"] = str(request.state.company_id)
    if hasattr(request.state, "application_id") and request.state.application_id:
        headers["X-Application-ID"] = str(request.state.application_id)
    if hasattr(request.state, "correlation_id") and request.state.correlation_id:
        headers["X-Correlation-ID"] = str(request.state.correlation_id)

    full_url = f"{target_url}{path}"
    if request.query_params:
        full_url = f"{full_url}?{request.query_params}"

    body = await request.body()

    try:
        response = await http_client.request(
            method=request.method,
            url=full_url,
            headers=headers,
            content=body if body else None
        )

        response_headers = dict(response.headers)
        response_headers.pop("content-encoding", None)
        response_headers.pop("content-length", None)
        response_headers.pop("transfer-encoding", None)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
    except httpx.ConnectError as e:
        print(f"[GATEWAY] Error de conexion a {full_url}: {e}")
        return JSONResponse(
            status_code=503,
            content={"detail": "Servicio no disponible"}
        )
    except httpx.TimeoutException as e:
        print(f"[GATEWAY] Timeout en {full_url}: {e}")
        return JSONResponse(
            status_code=504,
            content={"detail": "Timeout del servicio"}
        )
    except Exception as e:
        print(f"[GATEWAY] Error en proxy a {full_url}: {e}")
        return JSONResponse(
            status_code=502,
            content={"detail": "Error en el gateway"}
        )


@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth(request: Request, path: str):
    if not AUTH_SERVICE_URL:
        return JSONResponse(status_code=503, content={"detail": "Auth service no configurado"})
    return await proxy_request(request, AUTH_SERVICE_URL, f"/auth/{path}")


@router.api_route("/sessions", methods=["GET", "POST"])
async def proxy_sessions_root(request: Request):
    if not SESSION_SERVICE_URL:
        return JSONResponse(status_code=503, content={"detail": "Session service no configurado"})
    return await proxy_request(request, SESSION_SERVICE_URL, "/sessions")


@router.api_route("/sessions/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_sessions(request: Request, path: str):
    if not SESSION_SERVICE_URL:
        return JSONResponse(status_code=503, content={"detail": "Session service no configurado"})
    return await proxy_request(request, SESSION_SERVICE_URL, f"/sessions/{path}")


@router.api_route("/activities", methods=["GET", "POST"])
async def proxy_activities_root(request: Request):
    if not SESSION_SERVICE_URL:
        return JSONResponse(status_code=503, content={"detail": "Session service no configurado"})
    return await proxy_request(request, SESSION_SERVICE_URL, "/activities")


@router.api_route("/activities/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_activities(request: Request, path: str):
    if not SESSION_SERVICE_URL:
        return JSONResponse(status_code=503, content={"detail": "Session service no configurado"})
    return await proxy_request(request, SESSION_SERVICE_URL, f"/activities/{path}")


@router.api_route("/contents", methods=["GET", "POST"])
async def proxy_contents_root(request: Request):
    if not RECOMMENDATION_SERVICE_URL:
        return JSONResponse(status_code=503, content={"detail": "Recommendation service no configurado"})
    return await proxy_request(request, RECOMMENDATION_SERVICE_URL, "/contents")


@router.api_route("/contents/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_contents(request: Request, path: str):
    if not RECOMMENDATION_SERVICE_URL:
        return JSONResponse(status_code=503, content={"detail": "Recommendation service no configurado"})
    return await proxy_request(request, RECOMMENDATION_SERVICE_URL, f"/contents/{path}")


@router.api_route("/monitoring/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_monitoring(request: Request, path: str):
    if not MONITORING_SERVICE_URL:
        return JSONResponse(status_code=503, content={"detail": "Monitoring service no configurado"})
    return await proxy_request(request, MONITORING_SERVICE_URL, f"/{path}")


@router.api_route("/logs/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_logs(request: Request, path: str):
    if not LOG_SERVICE_URL:
        return JSONResponse(status_code=503, content={"detail": "Log service no configurado"})
    return await proxy_request(request, LOG_SERVICE_URL, f"/logs/{path}")


async def validate_api_key(api_key: str) -> dict:
    try:
        validation_url = f"{AUTH_SERVICE_URL}/auth/api-keys/validate"
        response = await http_client.post(
            validation_url,
            json={"key_value": api_key}
        )
        if response.status_code == 200:
            return response.json()
        return {"valid": False, "reason": "API key invalida"}
    except Exception as e:
        print(f"[GATEWAY WS] Error validando API key: {e}")
        return {"valid": False, "reason": str(e)}


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


async def connect_to_monitoring(monitoring_url: str, max_retries: int = 3, retry_delay: float = 1.0):
    last_exception = None
    for attempt in range(max_retries):
        try:
            monitoring_ws = await websockets.connect(
                monitoring_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )
            return monitoring_ws
        except Exception as e:
            last_exception = e
            print(f"[GATEWAY WS] Intento {attempt + 1}/{max_retries} fallido conectando a Monitoring: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
    
    raise last_exception


async def send_buffered_messages(monitoring_ws, buffer: deque) -> int:
    sent_count = 0
    while buffer:
        message = buffer.popleft()
        try:
            await monitoring_ws.send(message)
            sent_count += 1
        except Exception as e:
            buffer.appendleft(message)
            print(f"[GATEWAY WS] Error enviando mensaje del buffer: {e}")
            break
    return sent_count


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
    if not auth_result["valid"]:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=auth_result.get("reason", "No autorizado"))
        return

    company_id = auth_result.get("company_id")

    await websocket.accept()
    print(f"[GATEWAY WS] Conexion aceptada: session={session_id}, activity={activity_uuid}, company={company_id}")

    monitoring_url = build_monitoring_ws_url(session_id, activity_uuid)
    proxy_state = WebSocketProxyState()
    
    client_connected = True
    should_reconnect = True

    async def notify_client_status(status_type: str, message: str):
        try:
            await websocket.send_text(f'{{"type": "connection_status", "status": "{status_type}", "message": "{message}"}}')
        except Exception:
            pass

    while should_reconnect and client_connected:
        monitoring_ws = None
        try:
            if proxy_state.reconnect_attempts > 0:
                await notify_client_status("reconnecting", f"Reconectando al servicio (intento {proxy_state.reconnect_attempts})")
            
            monitoring_ws = await connect_to_monitoring(
                monitoring_url,
                max_retries=proxy_state.max_reconnect_attempts,
                retry_delay=proxy_state.reconnect_delay
            )
            
            proxy_state.is_connected = True
            proxy_state.reconnect_attempts = 0
            print(f"[GATEWAY WS] Conectado a Monitoring: {monitoring_url}")

            if proxy_state.pending_messages:
                sent = await send_buffered_messages(monitoring_ws, proxy_state.pending_messages)
                print(f"[GATEWAY WS] Enviados {sent} mensajes del buffer")

            await notify_client_status("connected", "Conectado al servicio de monitoreo")

            forward_to_monitoring_task = asyncio.create_task(
                forward_to_monitoring(websocket, monitoring_ws, proxy_state)
            )
            forward_to_client_task = asyncio.create_task(
                forward_to_client(websocket, monitoring_ws)
            )

            done, pending = await asyncio.wait(
                [forward_to_monitoring_task, forward_to_client_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            for task in done:
                exception = task.exception()
                if exception:
                    if isinstance(exception, WebSocketDisconnect):
                        print(f"[GATEWAY WS] Cliente desconectado: {activity_uuid}")
                        client_connected = False
                        should_reconnect = False
                    else:
                        print(f"[GATEWAY WS] Error en tarea: {exception}")

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"[GATEWAY WS] Conexion con Monitoring cerrada: {e}")
            proxy_state.is_connected = False
            proxy_state.reconnect_attempts += 1
            
            if proxy_state.reconnect_attempts >= proxy_state.max_reconnect_attempts:
                await notify_client_status("error", "No se pudo reconectar al servicio")
                should_reconnect = False
            else:
                await asyncio.sleep(proxy_state.reconnect_delay * proxy_state.reconnect_attempts)

        except Exception as e:
            print(f"[GATEWAY WS] Error conectando a Monitoring: {e}")
            proxy_state.reconnect_attempts += 1
            
            if proxy_state.reconnect_attempts >= proxy_state.max_reconnect_attempts:
                await notify_client_status("error", "Error conectando al servicio de monitoreo")
                should_reconnect = False
            else:
                await asyncio.sleep(proxy_state.reconnect_delay * proxy_state.reconnect_attempts)

        finally:
            if monitoring_ws:
                try:
                    await monitoring_ws.close()
                except Exception:
                    pass

    try:
        await websocket.close()
    except Exception:
        pass
    print(f"[GATEWAY WS] Conexion cerrada: {activity_uuid}")


async def forward_to_monitoring(client_ws: WebSocket, monitoring_ws, proxy_state: WebSocketProxyState):
    try:
        while True:
            data = await client_ws.receive_text()
            
            if proxy_state.is_connected:
                try:
                    await monitoring_ws.send(data)
                except Exception as e:
                    print(f"[GATEWAY WS] Error enviando a Monitoring, guardando en buffer: {e}")
                    proxy_state.pending_messages.append(data)
                    proxy_state.is_connected = False
                    raise
            else:
                proxy_state.pending_messages.append(data)
                print(f"[GATEWAY WS] Mensaje agregado al buffer (tamano: {len(proxy_state.pending_messages)})")
                
    except WebSocketDisconnect:
        print(f"[GATEWAY WS] Cliente desconectado")
        raise
    except Exception as e:
        print(f"[GATEWAY WS] Error recibiendo del cliente: {e}")
        raise


async def forward_to_client(client_ws: WebSocket, monitoring_ws):
    try:
        async for message in monitoring_ws:
            await client_ws.send_text(message)
    except websockets.exceptions.ConnectionClosed as e:
        print(f"[GATEWAY WS] Conexion de Monitoring cerrada: {e}")
        raise
    except Exception as e:
        print(f"[GATEWAY WS] Error recibiendo de Monitoring: {e}")
        raise