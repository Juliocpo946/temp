from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_NAME, SERVICE_PORT
from src.presentation.routes.email_routes import router as email_router
# Importar el consumer
from src.infrastructure.messaging.email_consumer import EmailConsumer

email_consumer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global email_consumer
    print(f"[MAIN] Iniciando {SERVICE_NAME}...")

    try:
        email_consumer = EmailConsumer()
        email_consumer.start()
        print("[MAIN] EmailConsumer iniciado correctamente")
    except Exception as e:
        print(f"[MAIN] Error fatal iniciando EmailConsumer: {e}")

    yield

    print(f"[MAIN] Deteniendo {SERVICE_NAME}...")


app = FastAPI(
    title="Email Service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(email_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": SERVICE_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)