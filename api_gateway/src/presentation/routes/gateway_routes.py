from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "api-gateway"}

@router.post("/proxy/{path:path}")
async def proxy_request(request: Request, path: str):
    company_id = getattr(request.state, 'company_id', None)
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    return {
        "message": "Solicitud ruteada",
        "path": path,
        "company_id": company_id,
        "correlation_id": correlation_id
    }