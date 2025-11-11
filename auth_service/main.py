from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.infrastructure.persistence.database import engine, Base
from src.infrastructure.config.settings import SERVICE_PORT
from src.presentation.routes.company_routes import auth_router
from src.presentation.routes.token_routes import token_routes
from src.presentation.routes.application_routes import application_routes

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Auth Service iniciado")
    yield
    print("Auth Service detenido")

app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(token_routes)
app.include_router(application_routes)

@app.get("/health")
def health_check(request: Request):
    client_ip = request.client.host
    allowed_ips = ["*"]
    
    if client_ip not in allowed_ips:
        return JSONResponse(
            status_code=403,
            content={"detail": "No autorizado"}
        )
    
    return {"status": "ok", "service": "auth-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)