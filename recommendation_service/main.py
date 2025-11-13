from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_PORT
from src.infrastructure.messaging.recommendation_consumer import RecommendationConsumer
from src.presentation.routes.health_routes import router

recommendation_consumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommendation_consumer
    recommendation_consumer = RecommendationConsumer()
    recommendation_consumer.start()
    print("[INFO] Recommendation Service iniciado y escuchando eventos de monitoreo")
    yield
    if recommendation_consumer:
        recommendation_consumer.rabbitmq_client.close()

app = FastAPI(
    title="Recommendation Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "recommendation-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)