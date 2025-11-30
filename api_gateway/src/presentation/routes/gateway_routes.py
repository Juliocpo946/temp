import asyncio
from typing import Optional
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