from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.domain.value_objects.correlation_id import CorrelationId
from src.infrastructure.http.http_client import HTTPClient
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.application.use_cases.validate_request import ValidateRequestUseCase
from src.application.use_cases.route_request import RouteRequestUseCase

class GatewayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, http_client: HTTPClient, rabbitmq_client: RabbitMQClient):
        super().__init__(app)
        self.http_client = http_client
        self.rabbitmq_client = rabbitmq_client
        self.validate_use_case = ValidateRequestUseCase(http_client, rabbitmq_client)
        self.route_use_case = RouteRequestUseCase(rabbitmq_client)

    async def dispatch(self, request: Request, call_next):
        correlation_id = str(CorrelationId())
        request.state.correlation_id = correlation_id

        excluded_paths = ['/health', '/docs', '/openapi.json', '/redoc', '/health/services']
        if request.url.path in excluded_paths:
            response = await call_next(request)
            return response

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            self.rabbitmq_client.publish('logs', {
                'service': 'api-gateway',
                'level': 'error',
                'message': 'Acceso denegado: falta token'
            })
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

        self.route_use_case.execute(
            correlation_id=correlation_id,
            token=token,
            service='unknown',
            method=request.method,
            path=request.url.path,
            status=response.status_code
        )

        return response