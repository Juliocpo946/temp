from fastapi import APIRouter, HTTPException, status
from src.application.use_cases.validate_jwt import ValidateJWTUseCase
from src.presentation.schemas.token_schema import ValidateTokenSchema, TokenValidationResponseSchema

router = APIRouter()

@router.post("/validate", response_model=TokenValidationResponseSchema)
def validate_token(request_data: ValidateTokenSchema):
    try:
        use_case = ValidateJWTUseCase()
        result = use_case.execute(request_data.token)
        
        if not result['valid']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('error', 'Token invalido')
            )
        
        return TokenValidationResponseSchema(
            valid=result['valid'],
            company_id=result.get('company_id'),
            email=result.get('email')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))