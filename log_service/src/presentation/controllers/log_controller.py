from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from src.infrastructure.persistence.repositories.log_repository_impl import LogRepositoryImpl
from src.application.use_cases.save_log import SaveLogUseCase
from src.application.use_cases.get_logs import GetLogsUseCase
from src.presentation.schemas.log_schema import LogCreateSchema, LogResponseSchema

router = APIRouter()

@router.post("/", response_model=dict)
def create_log(log_data: LogCreateSchema):
    try:
        log_repo = LogRepositoryImpl()
        use_case = SaveLogUseCase(log_repo)
        result = use_case.execute(log_data.service, log_data.level, log_data.message)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error al guardar log: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.get("/", response_model=dict)
def get_logs(
    service: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    try:
        log_repo = LogRepositoryImpl()
        use_case = GetLogsUseCase(log_repo)
        result = use_case.execute(service, level, limit)
        return result
    except Exception as e:
        print(f"Error al obtener logs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.get("/{service}", response_model=dict)
def get_logs_by_service(service: str, limit: int = Query(100, ge=1, le=1000)):
    try:
        log_repo = LogRepositoryImpl()
        use_case = GetLogsUseCase(log_repo)
        result = use_case.execute(service=service, limit=limit)
        return result
    except Exception as e:
        print(f"Error al obtener logs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")