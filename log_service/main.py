from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_PORT
from src.infrastructure.persistence.database import connect_db, disconnect_db
from src.infrastructure.messaging.log_consumer import LogConsumer
from src.presentation.routes.log_routes import log_routes

log_consumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global log_consumer
    connect_db()
    log_consumer = LogConsumer()
    log_consumer.start()
    print("Log Service iniciado y escuchando en la cola de logs")
    yield
    disconnect_db()
    if log_consumer:
        log_consumer.rabbitmq_client.close()

app = FastAPI(title="Log Service", version="1.0.0", lifespan=lifespan)

app.include_router(log_routes)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "log-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)