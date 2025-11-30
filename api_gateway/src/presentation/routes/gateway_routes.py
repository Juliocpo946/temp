from fastapi import APIRouter, Request
from src.infrastructure.http.http_client import HTTPClient
from src.infrastructure.config.settings import AUTH_SERVICE_URL, LOG_SERVICE_URL, SESSION_SERVICE_URL

router = APIRouter()
http_client = HTTPClient()

SERVICE_ROUTES = {
    "auth": AUTH_SERVICE_URL,
    "logs": LOG_SERVICE_URL,
    "sessions": SESSION_SERVICE_URL,
    "activities": SESSION_SERVICE_URL,
}

@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, service: str, path: str):
    if service not in SERVICE_ROUTES:
        return {"error": "Servicio no encontrado"}, 404
    
    url = f"{SERVICE_ROUTES[service]}/{service}/{path}"
    query_params = dict(request.query_params)
    
    print(f"[GATEWAY] {request.method} {url}")
    print(f"[GATEWAY] Path capturado: {path}")
    print(f"[GATEWAY] Query params: {query_params}")
    
    headers = {}
    if hasattr(request.state, 'company_id'):
        headers['X-Company-ID'] = str(request.state.company_id)
        print(f"[GATEWAY] X-Company-ID: {headers['X-Company-ID']}")
    if hasattr(request.state, 'auth_type'):
        headers['X-Auth-Type'] = request.state.auth_type
    
    try:
        body = None
        if request.method in ["POST", "PUT", "PATCH"] and request.headers.get("content-length"):
            try:
                body = await request.json()
            except:
                body = None
        
        if request.method == "GET":
            return await http_client.get(url, headers=headers, params=query_params)
        elif request.method == "POST":
            print(f"[GATEWAY] Enviando POST a {url}")
            result = await http_client.post(url, json=body, headers=headers, params=query_params)
            print(f"[GATEWAY] Respuesta recibida: {result}")
            return result
        elif request.method == "PUT":
            return await http_client.put(url, json=body, headers=headers, params=query_params)
        elif request.method == "PATCH":
            return await http_client.patch(url, json=body, headers=headers, params=query_params)
        elif request.method == "DELETE":
            return await http_client.delete(url, headers=headers, params=query_params)
        else:
            return await http_client.get(url, headers=headers, params=query_params)
    except Exception as e:
        print(f"[GATEWAY ERROR] {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}, 500