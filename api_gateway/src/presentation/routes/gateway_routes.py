from fastapi import APIRouter, Request
from src.infrastructure.http.http_client import HTTPClient
from src.infrastructure.config.settings import AUTH_SERVICE_URL, LOG_SERVICE_URL, SESSION_SERVICE_URL

router = APIRouter()
http_client = HTTPClient()

SERVICE_ROUTES = {
    "auth": AUTH_SERVICE_URL,
    "logs": LOG_SERVICE_URL,
    "sessions": SESSION_SERVICE_URL,
}

@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, service: str, path: str):
    if service not in SERVICE_ROUTES:
        return {"error": "Servicio no encontrado"}, 404
    
    url = f"{SERVICE_ROUTES[service]}/{service}/{path}"
    query_params = dict(request.query_params)
    
    try:
        if request.method == "GET":
            return await http_client.get(url, params=query_params)
        elif request.method == "POST":
            body = await request.json() if request.headers.get("content-length") else {}
            return await http_client.post(url, json=body, params=query_params)
        elif request.method in ["PUT", "PATCH"]:
            body = await request.json() if request.headers.get("content-length") else {}
            return await http_client.post(url, json=body, params=query_params)
        elif request.method == "DELETE":
            return await http_client.get(url, params=query_params)
        else:
            return await http_client.get(url, params=query_params)
    except Exception as e:
        return {"error": str(e)}, 500