from fastapi import FastAPI
from src.infrastructure.config.settings import SERVICE_PORT
from src.presentation.routes.websocket_routes import router

app = FastAPI(
    title="Cognitive Service",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "cognitive-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)