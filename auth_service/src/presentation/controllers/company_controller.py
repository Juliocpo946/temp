from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.company_repository_impl import CompanyRepositoryImpl
from src.infrastructure.persistence.repositories.token_repository_impl import TokenRepositoryImpl
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.register_company import RegisterCompanyUseCase
from src.application.use_cases.get_company import GetCompanyUseCase
from src.application.use_cases.update_company import UpdateCompanyUseCase
from src.presentation.schemas.company_schema import CompanyCreateSchema, CompanyUpdateSchema, CompanyResponseSchema

router = APIRouter()
rabbitmq_client = RabbitMQClient()

@router.post("/register", response_model=dict)
def register_company(company: CompanyCreateSchema, db: Session = Depends(get_db)):
    try:
        company_repo = CompanyRepositoryImpl(db)
        token_repo = TokenRepositoryImpl(db)
        use_case = RegisterCompanyUseCase(company_repo, token_repo, rabbitmq_client)
        result = use_case.execute(company.name, company.email)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error al registrar empresa: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.get("/{company_id}", response_model=dict)
def get_company(company_id: int, db: Session = Depends(get_db)):
    try:
        company_repo = CompanyRepositoryImpl(db)
        use_case = GetCompanyUseCase(company_repo, rabbitmq_client)
        result = use_case.execute(company_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(f"Error al obtener empresa: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.put("/{company_id}", response_model=dict)
def update_company(company_id: int, company_data: CompanyUpdateSchema, db: Session = Depends(get_db)):
    try:
        company_repo = CompanyRepositoryImpl(db)
        use_case = UpdateCompanyUseCase(company_repo, rabbitmq_client)
        result = use_case.execute(company_id, company_data.name, company_data.email, company_data.is_active)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error al actualizar empresa: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")