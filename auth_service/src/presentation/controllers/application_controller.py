from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.application_repository_impl import ApplicationRepositoryImpl
from src.infrastructure.persistence.repositories.company_repository_impl import CompanyRepositoryImpl
from src.infrastructure.persistence.repositories.token_repository_impl import TokenRepositoryImpl
from src.infrastructure.persistence.repositories.revocation_token_repository_impl import RevocationTokenRepositoryImpl
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.create_application import CreateApplicationUseCase
from src.application.use_cases.get_applications import GetApplicationsUseCase
from src.application.use_cases.get_application import GetApplicationUseCase
from src.application.use_cases.generate_new_api_key import GenerateNewApiKeyUseCase
from src.application.use_cases.request_revoke_api_key import RequestRevokeApiKeyUseCase
from src.application.use_cases.confirm_revoke_api_key import ConfirmRevokeApiKeyUseCase
from src.presentation.schemas.application_schema import ApplicationCreateSchema, ApiKeyResponseSchema, ConfirmRevokeSchema

router = APIRouter()
rabbitmq_client = RabbitMQClient()

@router.post("/", response_model=dict)
def create_application(application_data: ApplicationCreateSchema, company_id: str, db: Session = Depends(get_db)):
    try:
        application_repo = ApplicationRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        token_repo = TokenRepositoryImpl(db)
        use_case = CreateApplicationUseCase(application_repo, company_repo, token_repo, rabbitmq_client)
        result = use_case.execute(company_id, application_data.name, application_data.platform, application_data.environment)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error al crear aplicacion: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.get("/", response_model=dict)
def get_applications(company_id: str, db: Session = Depends(get_db)):
    try:
        application_repo = ApplicationRepositoryImpl(db)
        use_case = GetApplicationsUseCase(application_repo, rabbitmq_client)
        result = use_case.execute(company_id)
        return result
    except Exception as e:
        print(f"Error al obtener aplicaciones: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.get("/{application_id}", response_model=dict)
def get_application(application_id: str, db: Session = Depends(get_db)):
    try:
        application_repo = ApplicationRepositoryImpl(db)
        use_case = GetApplicationUseCase(application_repo, rabbitmq_client)
        result = use_case.execute(application_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(f"Error al obtener aplicacion: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.post("/{application_id}/generate-key", response_model=ApiKeyResponseSchema)
def generate_api_key(application_id: str, db: Session = Depends(get_db)):
    try:
        application_repo = ApplicationRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        token_repo = TokenRepositoryImpl(db)
        use_case = GenerateNewApiKeyUseCase(application_repo, company_repo, token_repo, rabbitmq_client)
        result = use_case.execute(application_id)
        return ApiKeyResponseSchema(api_key=result['api_key'])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error al generar API key: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.post("/api-keys/{api_key_id}/request-revoke", response_model=dict)
def request_revoke_api_key(api_key_id: str, db: Session = Depends(get_db)):
    try:
        token_repo = TokenRepositoryImpl(db)
        application_repo = ApplicationRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        revocation_token_repo = RevocationTokenRepositoryImpl(db)
        use_case = RequestRevokeApiKeyUseCase(token_repo, application_repo, company_repo, revocation_token_repo, rabbitmq_client)
        result = use_case.execute(api_key_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(f"Error al solicitar revocacion: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.post("/api-keys/{api_key_id}/confirm-revoke", response_model=dict)
def confirm_revoke_api_key(api_key_id: str, confirm_data: ConfirmRevokeSchema, db: Session = Depends(get_db)):
    try:
        token_repo = TokenRepositoryImpl(db)
        application_repo = ApplicationRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        revocation_token_repo = RevocationTokenRepositoryImpl(db)
        use_case = ConfirmRevokeApiKeyUseCase(token_repo, application_repo, company_repo, revocation_token_repo, rabbitmq_client)
        result = use_case.execute(api_key_id, confirm_data.confirmation_code)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error al confirmar revocacion: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")