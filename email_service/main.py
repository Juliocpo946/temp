from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_PORT
from src.infrastructure.messaging.email_consumer import EmailConsumer
from src.presentation.routes.email_routes import router

email_consumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global email_consumer
    email_consumer = EmailConsumer()
    email_consumer.start()
    print("Email Service iniciado y escuchando en la cola de eventos")
    yield
    if email_consumer:
        email_consumer.rabbitmq_client.close()

app = FastAPI(
    title="Email Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "email-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)