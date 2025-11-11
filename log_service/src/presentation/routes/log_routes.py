from fastapi import APIRouter
from src.presentation.controllers.log_controller import router as log_router

log_routes = APIRouter(prefix="/logs", tags=["logs"])
log_routes.include_router(log_router)