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
            '/auth/companies/request-verification',
            '/auth/companies/register',
            '/auth/companies/login',
            '/auth/companies/verify-login',
            '/auth/api-keys/validate'
        ]
        
        admin_paths = [
            '/auth/applications',
            '/auth/companies/',
            '/auth/api-keys/by-key-value'
        ]
        
        if request.url.path in public_paths or any(request.url.path.startswith(p) for p in public_paths):
            response = await call_next(request)
            return response

        is_admin_operation = any(request.url.path.startswith(p) for p in admin_paths)
        
        if is_admin_operation:
            return await self._validate_jwt(request, call_next)
        else:
            return await self._validate_api_key(request, call_next)

    async def _validate_jwt(self, request: Request, call_next):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token JWT requerido"}
            )
        
        token = auth_header.split(' ')[1]
        
        validation_result = await self._validate_jwt_token(token)
        
        if not validation_result['valid']:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token invalido o expirado"}
            )
        
        request.state.company_id = validation_result['company_id']
        request.state.auth_type = 'jwt'
        
        response = await call_next(request)
        return response

    async def _validate_api_key(self, request: Request, call_next):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key requerida"}
            )

        key_value = auth_header.split(' ')[1]
        
        cached_data = self.redis_client.get_api_key(key_value)
        
        if cached_data:
            if not cached_data.get('is_active'):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "API key inactiva"}
                )
            
            request.state.company_id = cached_data.get('company_id')
            request.state.application_id = cached_data.get('application_id')
            request.state.api_key = key_value
            request.state.auth_type = 'api_key'
        else:
            validation_result = await self._validate_with_auth_service(key_value)
            
            if not validation_result['valid']:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "API key invalida"}
                )
            
            cache_data = {
                'company_id': validation_result['company_id'],
                'application_id': validation_result.get('application_id'),
                'is_active': True
            }
            self.redis_client.set_api_key(key_value, cache_data, ttl=3600)
            
            request.state.company_id = validation_result['company_id']
            request.state.application_id = validation_result.get('application_id')
            request.state.api_key = key_value
            request.state.auth_type = 'api_key'

        if hasattr(request.state, 'application_id') and request.state.application_id:
            today = datetime.utcnow().strftime('%Y-%m-%d')
            self.redis_client.increment_usage(request.state.application_id, today)

        response = await call_next(request)
        return response

    async def _validate_jwt_token(self, token: str) -> dict:
        try:
            validation_url = f"{AUTH_SERVICE_URL}/auth/token/validate"
            response = await self.http_client.post(
                validation_url,
                json={"token": token}
            )
            return response
        except Exception as e:
            print(f"Error al validar JWT token: {str(e)}")
            return {'valid': False, 'company_id': None}

    async def _validate_with_auth_service(self, key_value: str) -> dict:
        try:
            validation_url = f"{AUTH_SERVICE_URL}/auth/api-keys/validate"
            response = await self.http_client.post(
                validation_url,
                json={"key_value": key_value}
            )
            return response
        except Exception as e:
            print(f"Error al validar API key: {str(e)}")
            return {'valid': False, 'company_id': None, 'application_id': None}