from fastapi import APIRouter
from src.presentation.controllers.activity_controller import router as activity_router

router = APIRouter(prefix="/activities", tags=["activities"])
router.include_router(activity_router)