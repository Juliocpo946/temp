import jwt
from src.infrastructure.config.settings import JWT_SECRET_KEY, JWT_ALGORITHM

class ValidateJWTUseCase:
    def execute(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            if payload.get('type') != 'access':
                return {'valid': False, 'company_id': None}
            
            return {
                'valid': True,
                'company_id': payload.get('company_id'),
                'email': payload.get('email')
            }
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'company_id': None, 'error': 'Token expirado'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'company_id': None, 'error': 'Token invalido'}
        except Exception as e:
            return {'valid': False, 'company_id': None, 'error': str(e)}