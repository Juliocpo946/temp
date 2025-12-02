import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_PORT
from src.infrastructure.persistence.database import create_tables
from src.presentation.routes.payment_routes import router as payment_router
from src.presentation.routes.health_routes import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Payment Service iniciado")
    create_tables()
    yield
    print("Payment Service detenido")

app = FastAPI(title="Payment Service", version="1.0.0", lifespan=lifespan)

app.include_router(health_router)
app.include_router(payment_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)