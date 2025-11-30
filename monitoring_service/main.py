from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_PORT, SERVICE_NAME
from src.infrastructure.persistence.database import engine, Base
from src.infrastructure.ml.model_loader import ModelLoader
from src.presentation.routes.health_routes import router as health_router
from src.presentation.routes.ws_routes import router as ws_router

model_loader = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_loader
    Base.metadata.create_all(bind=engine)
    model_loader = ModelLoader()
    model_loader.load()
    print(f"[INFO] {SERVICE_NAME} iniciado en puerto {SERVICE_PORT}")
    yield
    if model_loader:
        model_loader.unload()

app = FastAPI(
    title="Monitoring Service",
    version="1.0.0",
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