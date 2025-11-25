from fastapi import APIRouter
from src.presentation.controllers.company_controller import router as company_router
from src.presentation.controllers.token_controller import router as token_router

auth_router = APIRouter(prefix="/auth", tags=["auth"])
auth_router.include_router(company_router, prefix="/companies")
auth_router.include_router(token_router, prefix="/token")