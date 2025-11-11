from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.domain.value_objects.correlation_id import CorrelationId
from src.infrastructure.http.http_client import HTTPClient
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import AUTH_SERVICE_URL

class GatewayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, http_client: HTTPClient, rabbitmq_client: RabbitMQClient, redis_client: RedisClient):
        super().__init__(app)
        self.http_client = http_client
        self.rabbitmq_client = rabbitmq_client
        self.redis_client = redis_client

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
        
        cached_data = self.redis_client.get_api_key(token)
        
        if cached_data:
            if not cached_data.get('is_active'):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token inactivo"}
                )
            
            request.state.company_id = cached_data.get('company_id')
            request.state.application_id = cached_data.get('application_id')
            request.state.token = token
        else:
            validation_result = await self._validate_with_auth_service(token)
            
            if not validation_result['valid']:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token invalido"}
                )
            
            cache_data = {
                'company_id': validation_result['company_id'],
                'application_id': validation_result.get('application_id'),
                'is_active': True
            }
            self.redis_client.set_api_key(token, cache_data, ttl=3600)
            
            request.state.company_id = validation_result['company_id']
            request.state.application_id = validation_result.get('application_id')
            request.state.token = token

        if hasattr(request.state, 'application_id') and request.state.application_id:
            today = datetime.utcnow().strftime('%Y-%m-%d')
            self.redis_client.increment_usage(request.state.application_id, today)

        response = await call_next(request)

        return response

    async def _validate_with_auth_service(self, token: str) -> dict:
        try:
            validation_url = f"{AUTH_SERVICE_URL}/auth/tokens/validate"
            response = await self.http_client.post(
                validation_url,
                json={"token": token}
            )
            return response
        except Exception as e:
            print(f"Error al validar token: {str(e)}")
            return {'valid': False, 'company_id': None, 'application_id': None}