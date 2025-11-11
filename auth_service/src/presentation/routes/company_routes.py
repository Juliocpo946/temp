from fastapi import APIRouter
from src.presentation.controllers.company_controller import router as company_router

auth_router = APIRouter(prefix="/auth", tags=["auth"])
auth_router.include_router(company_router, prefix="/companies")
