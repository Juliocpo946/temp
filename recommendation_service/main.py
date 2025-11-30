from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_PORT
from src.infrastructure.persistence.database import create_tables
from src.infrastructure.messaging.intervention_consumer import InterventionConsumer
from src.presentation.routes.health_routes import router as health_router
from src.presentation.routes.content_routes import router as content_router

intervention_consumer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global intervention_consumer
    create_tables()
    intervention_consumer = InterventionConsumer()
    intervention_consumer.start()
    yield
    if intervention_consumer:
        intervention_consumer.close()


app = FastAPI(
    title="Recommendation Service",
    version="2.0.0",
    lifespan=lifespan
)

app.include_router(health_router)
app.include_router(content_router, prefix="/contents", tags=["Contents"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)