from fastapi import APIRouter
from src.infrastructure.config.settings import SERVICE_NAME
from src.infrastructure.ml.model_loader import ModelLoader

router = APIRouter()

@router.get("/health")
def health_check():
    model_loader = ModelLoader()
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "model_loaded": model_loader.is_loaded
    }

@router.get("/ready")
def readiness_check():
    return {"status": "ready"}