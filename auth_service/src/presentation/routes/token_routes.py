from fastapi import APIRouter
from src.presentation.controllers.token_controller import router as token_router

token_routes = APIRouter(prefix="/auth/tokens", tags=["tokens"])
token_routes.include_router(token_router)
