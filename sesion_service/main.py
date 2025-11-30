from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.persistence.database import engine, Base
from src.infrastructure.config.settings import SERVICE_PORT
from src.infrastructure.messaging.websocket_event_consumer import WebsocketEventConsumer
from src.presentation.routes.session_routes import router as session_router
from src.presentation.routes.activity_routes import router as activity_router

websocket_consumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global websocket_consumer
    
    Base.metadata.create_all(bind=engine)
    
    websocket_consumer = WebsocketEventConsumer()
    websocket_consumer.start()
    
    print("[INFO] Session Service iniciado")
    yield
    
    if websocket_consumer:
        websocket_consumer.rabbitmq_client.close()
    print("[INFO] Session Service detenido")

app = FastAPI(
    title="Session Service",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.include_router(session_router)
app.include_router(activity_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "session-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)