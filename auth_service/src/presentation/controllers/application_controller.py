from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.application_repository_impl import ApplicationRepositoryImpl
from src.infrastructure.persistence.repositories.company_repository_impl import CompanyRepositoryImpl
from src.infrastructure.persistence.repositories.api_key_repository_impl import ApiKeyRepositoryImpl
from src.infrastructure.persistence.repositories.revocation_api_key_repository_impl import RevocationApiKeyRepositoryImpl
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.create_application import CreateApplicationUseCase
from src.application.use_cases.get_applications import GetApplicationsUseCase
from src.application.use_cases.get_application import GetApplicationUseCase
from src.application.use_cases.generate_new_api_key import GenerateNewApiKeyUseCase
from src.application.use_cases.request_revoke_api_key import RequestRevokeApiKeyUseCase
from src.application.use_cases.confirm_revoke_api_key import ConfirmRevokeApiKeyUseCase
from src.presentation.schemas.application_schema import ApplicationCreateSchema, ApiKeyResponseSchema, ConfirmRevokeSchema
import traceback

router = APIRouter()
rabbitmq_client = RabbitMQClient()

@router.post("/")
async def create_application(application_data: ApplicationCreateSchema, company_id: str = Query(...), db: Session = Depends(get_db)):
    try:
        application_repo = ApplicationRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        api_key_repo = ApiKeyRepositoryImpl(db)
        use_case = CreateApplicationUseCase(application_repo, company_repo, api_key_repo, rabbitmq_client)
        result = use_case.execute(company_id, application_data.name, application_data.platform, application_data.environment)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error detallado: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/")
async def get_applications(company_id: str = Query(...), db: Session = Depends(get_db)):
    try:
        application_repo = ApplicationRepositoryImpl(db)
        use_case = GetApplicationsUseCase(application_repo, rabbitmq_client)
        result = use_case.execute(company_id)
        return result
    except Exception as e:
        print(f"Error detallado: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{application_id}")
async def get_application(application_id: str, db: Session = Depends(get_db)):
    try:
        application_repo = ApplicationRepositoryImpl(db)
        use_case = GetApplicationUseCase(application_repo, rabbitmq_client)
        result = use_case.execute(application_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(f"Error detallado: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{application_id}/generate-key")
async def generate_api_key(application_id: str, db: Session = Depends(get_db)):
    try:
        application_repo = ApplicationRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        api_key_repo = ApiKeyRepositoryImpl(db)
        use_case = GenerateNewApiKeyUseCase(application_repo, company_repo, api_key_repo, rabbitmq_client)
        result = use_case.execute(application_id)
        return ApiKeyResponseSchema(api_key=result['api_key'])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error detallado: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/api-keys/{api_key_id}/request-revoke")
async def request_revoke_api_key(api_key_id: str, db: Session = Depends(get_db)):
    try:
        api_key_repo = ApiKeyRepositoryImpl(db)
        application_repo = ApplicationRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        revocation_api_key_repo = RevocationApiKeyRepositoryImpl(db)
        use_case = RequestRevokeApiKeyUseCase(api_key_repo, application_repo, company_repo, revocation_api_key_repo, rabbitmq_client)
        result = use_case.execute(api_key_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(f"Error detallado: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/api-keys/{api_key_id}/confirm-revoke")
async def confirm_revoke_api_key(api_key_id: str, confirm_data: ConfirmRevokeSchema, db: Session = Depends(get_db)):
    try:
        api_key_repo = ApiKeyRepositoryImpl(db)
        application_repo = ApplicationRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        revocation_api_key_repo = RevocationApiKeyRepositoryImpl(db)
        use_case = ConfirmRevokeApiKeyUseCase(api_key_repo, application_repo, company_repo, revocation_api_key_repo, rabbitmq_client)
        result = use_case.execute(api_key_id, confirm_data.confirmation_code)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error detallado: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))