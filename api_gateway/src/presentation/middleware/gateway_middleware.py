from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.domain.value_objects.correlation_id import CorrelationId
from src.infrastructure.http.http_client import HTTPClient
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.validate_request import ValidateRequestUseCase

class GatewayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, http_client: HTTPClient, rabbitmq_client: RabbitMQClient):
        super().__init__(app)
        self.http_client = http_client
        self.rabbitmq_client = rabbitmq_client
        self.validate_use_case = ValidateRequestUseCase(http_client, rabbitmq_client)

    async def dispatch(self, request: Request, call_next):
        correlation_id = str(CorrelationId())
        request.state.correlation_id = correlation_id

        public_paths = [
            '/health',
            '/docs',
            '/openapi.json',
            '/redoc',
            '/health/services',
            '/auth/auth/companies/register',
            '/auth/auth/tokens/validate',
            '/auth/health',
            '/logs/health',
            '/logs/logs/'
        ]
        
        if request.url.path in public_paths or any(request.url.path.startswith(p) for p in public_paths):
            response = await call_next(request)
            return response

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token requerido"}
            )

        token = auth_header.split(' ')[1]
        validation_result = await self.validate_use_case.execute(token)
        
        if not validation_result['valid']:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token inválido"}
            )

        request.state.company_id = validation_result['company_id']
        request.state.token = token
        response = await call_next(request)

        return response