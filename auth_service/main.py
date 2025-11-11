from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.persistence.database import engine, Base
from src.infrastructure.config.settings import SERVICE_PORT
from src.presentation.routes.company_routes import auth_router
from src.presentation.routes.api_key_routes import api_key_routes
from src.presentation.routes.application_routes import application_routes

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Auth Service iniciado")
    yield
    print("Auth Service detenido")

app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(api_key_routes)
app.include_router(application_routes)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)