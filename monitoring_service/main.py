from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_PORT, SERVICE_NAME
from src.infrastructure.persistence.database import engine, Base
from src.infrastructure.ml.model_loader import ModelLoader
from src.infrastructure.messaging.activity_event_consumer import ActivityEventConsumer
from src.presentation.routes.health_routes import router as health_router
from src.presentation.routes.ws_routes import router as ws_router

model_loader = None
activity_consumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_loader, activity_consumer
    
    Base.metadata.create_all(bind=engine)
    
    model_loader = ModelLoader()
    model_loader.load()
    
    activity_consumer = ActivityEventConsumer()
    activity_consumer.start()
    
    print(f"[INFO] {SERVICE_NAME} iniciado en puerto {SERVICE_PORT}")
    yield
    
    if model_loader:
        model_loader.unload()
    if activity_consumer:
        activity_consumer.rabbitmq_client.close()
    
    print(f"[INFO] {SERVICE_NAME} detenido")

app = FastAPI(
    title="Monitoring Service",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.include_router(health_router)
app.include_router(ws_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)