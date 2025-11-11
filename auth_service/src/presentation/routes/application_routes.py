from fastapi import APIRouter
from src.presentation.controllers.application_controller import router as application_router

application_routes = APIRouter(prefix="/auth/applications", tags=["applications"])
application_routes.include_router(application_router)