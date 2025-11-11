from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.repositories.api_key_repository_impl import ApiKeyRepositoryImpl
from src.infrastructure.persistence.repositories.company_repository_impl import CompanyRepositoryImpl
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.validate_api_key import ValidateApiKeyUseCase
from src.presentation.schemas.api_key_schema import ApiKeyValidationRequestSchema, ApiKeyValidationResponseSchema

router = APIRouter()
rabbitmq_client = RabbitMQClient()

@router.post("/validate", response_model=ApiKeyValidationResponseSchema)
def validate_api_key(request_data: ApiKeyValidationRequestSchema, db: Session = Depends(get_db)):
    try:
        api_key_repo = ApiKeyRepositoryImpl(db)
        company_repo = CompanyRepositoryImpl(db)
        use_case = ValidateApiKeyUseCase(api_key_repo, company_repo, rabbitmq_client)
        result = use_case.execute(request_data.key_value)
        return ApiKeyValidationResponseSchema(
            valid=result['valid'],
            company_id=result.get('company_id'),
            application_id=result.get('application_id')
        )
    except Exception as e:
        print(f"Error al validar API key: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")