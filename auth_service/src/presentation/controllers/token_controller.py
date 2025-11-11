from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.token_repository_impl import TokenRepositoryImpl
from src.infrastructure.persistence.repositories.company_repository_impl import CompanyRepositoryImpl
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.generate_token import GenerateTokenUseCase
from src.application.use_cases.validate_token import ValidateTokenUseCase
from src.application.use_cases.revoke_token import RevokeTokenUseCase
from src.presentation.schemas.token_schema import TokenGenerateSchema, TokenRevokeSchema, TokenResponseSchema, TokenValidationResponseSchema

router = APIRouter()
rabbitmq_client = RabbitMQClient()

@router.post("/generate", response_model=TokenResponseSchema)
def generate_token(token_data: TokenGenerateSchema, db: Session = Depends(get_db)):
    try:
        token_repo = TokenRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        use_case = GenerateTokenUseCase(token_repo, company_repo, rabbitmq_client)
        result = use_case.execute(token_data.company_id)
        return TokenResponseSchema(token=result['token'])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error al generar token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.post("/validate", response_model=TokenValidationResponseSchema)
def validate_token(token_data: TokenRevokeSchema, db: Session = Depends(get_db)):
    try:
        token_repo = TokenRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        use_case = ValidateTokenUseCase(token_repo, company_repo, rabbitmq_client)
        result = use_case.execute(token_data.token)
        return TokenValidationResponseSchema(valid=result['valid'], company_id=result['company_id'])
    except Exception as e:
        print(f"Error al validar token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

@router.post("/revoke")
def revoke_token(token_data: TokenRevokeSchema, db: Session = Depends(get_db)):
    try:
        token_repo = TokenRepositoryImpl(db)
        use_case = RevokeTokenUseCase(token_repo, rabbitmq_client)
        result = use_case.execute(token_data.token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(f"Error al revocar token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")
