from fastapi import APIRouter
from src.presentation.controllers.api_key_controller import router as api_key_router

api_key_routes = APIRouter(prefix="/auth/api-keys", tags=["api-keys"])
api_key_routes.include_router(api_key_router)