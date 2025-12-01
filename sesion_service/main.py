from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_PORT
from src.infrastructure.persistence.database import create_tables
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.activity_details_consumer import ActivityDetailsConsumer
from src.infrastructure.messaging.websocket_event_consumer import WebsocketEventConsumer
from src.presentation.controllers.session_controller import router as session_router
from src.presentation.controllers.activity_controller import router as activity_router

rabbitmq_client = None
activity_details_consumer = None
websocket_event_consumer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbitmq_client, activity_details_consumer, websocket_event_consumer
    print(f"[MAIN] [INFO] Iniciando Session Service...")
    create_tables()
    
    rabbitmq_client = RabbitMQClient()
    
    activity_details_consumer = ActivityDetailsConsumer(rabbitmq_client)
    activity_details_consumer.start()
    
    websocket_event_consumer = WebsocketEventConsumer()
    websocket_event_consumer.start()
    
    print(f"[MAIN] [INFO] Session Service iniciado correctamente")
    yield
    
    if rabbitmq_client:
        rabbitmq_client.close()
    if websocket_event_consumer:
        websocket_event_consumer.rabbitmq_client.close()
    print(f"[MAIN] [INFO] Session Service detenido")


app = FastAPI(
    title="Session Service",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "session-service"}


@app.get("/ready")
def readiness_check():
    return {"status": "ready"}


app.include_router(session_router, prefix="/sessions", tags=["Sessions"])
app.include_router(activity_router, prefix="/activities", tags=["Activities"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)