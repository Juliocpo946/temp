from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.infrastructure.config.settings import SERVICE_PORT, AUTH_SERVICE_URL, LOG_SERVICE_URL
from src.infrastructure.http.http_client import HTTPClient
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.presentation.middleware.gateway_middleware import GatewayMiddleware
from src.presentation.routes.gateway_routes import router

http_client = HTTPClient()
rabbitmq_client = RabbitMQClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API Gateway iniciado")
    yield
    await http_client.close()
    rabbitmq_client.close()
    print("API Gateway detenido")

app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(GatewayMiddleware, http_client=http_client, rabbitmq_client=rabbitmq_client)
app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "api-gateway"}

@app.get("/health/services")
async def health_check_services():
    try:
        auth_response = await http_client.get(f"{AUTH_SERVICE_URL}/health")
        log_response = await http_client.get(f"{LOG_SERVICE_URL}/health")
        
        return {
            "status": "ok",
            "services": {
                "auth-service": auth_response,
                "log-service": log_response
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)