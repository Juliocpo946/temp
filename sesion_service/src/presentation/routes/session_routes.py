from fastapi import APIRouter
from src.presentation.controllers.session_controller import router as session_router

router = APIRouter(prefix="/sessions", tags=["sessions"])
router.include_router(session_router)