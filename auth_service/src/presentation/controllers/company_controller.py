from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.company_repository_impl import CompanyRepositoryImpl
from src.infrastructure.persistence.repositories.api_key_repository_impl import ApiKeyRepositoryImpl
from src.infrastructure.persistence.repositories.email_verification_repository_impl import EmailVerificationRepositoryImpl
from src.infrastructure.persistence.repositories.login_attempt_repository_impl import LoginAttemptRepositoryImpl
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.request_email_verification import RequestEmailVerificationUseCase
from src.application.use_cases.confirm_email_verification import ConfirmEmailVerificationUseCase
from src.application.use_cases.request_login import RequestLoginUseCase
from src.application.use_cases.verify_login import VerifyLoginUseCase
from src.application.use_cases.validate_jwt import ValidateJWTUseCase
from src.application.use_cases.get_company import GetCompanyUseCase
from src.application.use_cases.update_company import UpdateCompanyUseCase
from src.presentation.schemas.verification_schema import RequestVerificationSchema, ConfirmVerificationSchema
from src.presentation.schemas.login_schema import RequestLoginSchema, VerifyLoginSchema
from src.presentation.schemas.token_schema import ValidateTokenSchema
from src.presentation.schemas.company_schema import CompanyUpdateSchema

router = APIRouter()
rabbitmq_client = RabbitMQClient()

@router.post("/request-verification", response_model=dict)
def request_verification(request_data: RequestVerificationSchema, db: Session = Depends(get_db)):
    try:
        company_repo = CompanyRepositoryImpl(db)
        email_verification_repo = EmailVerificationRepositoryImpl(db)
        use_case = RequestEmailVerificationUseCase(company_repo, email_verification_repo, rabbitmq_client)
        result = use_case.execute(request_data.name, request_data.email)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/register", response_model=dict)
def register_company(confirm_data: ConfirmVerificationSchema, db: Session = Depends(get_db)):
    try:
        company_repo = CompanyRepositoryImpl(db)
        api_key_repo = ApiKeyRepositoryImpl(db)
        email_verification_repo = EmailVerificationRepositoryImpl(db)
        use_case = ConfirmEmailVerificationUseCase(company_repo, api_key_repo, email_verification_repo, rabbitmq_client)
        result = use_case.execute(confirm_data.name, confirm_data.email, confirm_data.verification_code)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/login", response_model=dict)
def request_login(request_data: RequestLoginSchema, db: Session = Depends(get_db)):
    try:
        company_repo = CompanyRepositoryImpl(db)
        login_attempt_repo = LoginAttemptRepositoryImpl(db)
        use_case = RequestLoginUseCase(company_repo, login_attempt_repo, rabbitmq_client)
        result = use_case.execute(request_data.email)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/verify-login", response_model=dict)
def verify_login(verify_data: VerifyLoginSchema, db: Session = Depends(get_db)):
    try:
        company_repo = CompanyRepositoryImpl(db)
        login_attempt_repo = LoginAttemptRepositoryImpl(db)
        use_case = VerifyLoginUseCase(company_repo, login_attempt_repo)
        result = use_case.execute(verify_data.email, verify_data.otp_code)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{company_id}", response_model=dict)
def get_company(
    company_id: str, 
    db: Session = Depends(get_db),
    x_company_id: str = Header(None, alias="X-Company-ID")
):
    try:
        if not x_company_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Company ID requerido")
        
        if x_company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para ver esta empresa")
        
        company_repo = CompanyRepositoryImpl(db)
        use_case = GetCompanyUseCase(company_repo, rabbitmq_client)
        result = use_case.execute(company_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{company_id}", response_model=dict)
def update_company(
    company_id: str, 
    company_data: CompanyUpdateSchema, 
    db: Session = Depends(get_db),
    x_company_id: str = Header(None, alias="X-Company-ID")
):
    try:
        if not x_company_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Company ID requerido")
        
        if x_company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para modificar esta empresa")
        
        company_repo = CompanyRepositoryImpl(db)
        use_case = UpdateCompanyUseCase(company_repo, rabbitmq_client)
        result = use_case.execute(company_id, company_data.name, company_data.email, company_data.is_active)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))