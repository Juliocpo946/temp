# API Gateway - Arquitectura y Flujo

## Descripción General

El API Gateway actúa como punto de entrada único para todas las peticiones. Valida tokens contra Auth Service y ruteador las peticiones a servicios internos. Implementa middleware de seguridad y publica logs en RabbitMQ.

## Flujo de Negocio

### 1. Petición Entrante

```
Cliente (app/web)
   ↓
Envía petición con Bearer token
   ↓
API Gateway intercepta
   ↓
Middleware verifica header Authorization
   ↓
Extrae token
   ↓
Consulta Auth Service: ¿token válido?
   ↓
Auth Service responde válido/inválido
   ↓
Si válido: continúa, adiciona company_id a request
Si inválido: responde 401 Unauthorized
   ↓
Ruteador a servicio interno (si está implementado)
   ↓
Devuelve respuesta al cliente
   ↓
Publica log en RabbitMQ
```

### 2. Generación de Correlation ID

```
Cada petición recibe un correlation_id único
   ↓
Se propaga en logs para rastreo
   ↓
Permite auditar flujo completo de una request
```

### 3. Flujo de Validación

```
Authorization: Bearer abc123xyz
   ↓
Validar formato "Bearer xxxxxx"
   ↓
Extraer token
   ↓
POST /auth/tokens/validate
   ↓
Si valid=true:
  - Guardar company_id en request.state
  - Guardar token en request.state
  - Permitir acceso
   ↓
Si valid=false:
  - Responder 401
  - Publicar log de acceso denegado
```

## Arquitectura por Capas

### Domain Layer
- **Entities**: Request (auditoría de peticiones)
- **Value Objects**: CorrelationId (UUID único por request)
- **Repositories**: Interfaz para logging (optional)

### Application Layer
- **Use Cases**:
  - ValidateRequest: Valida token contra Auth Service
  - RouteRequest: Registra petición rutoeada
- **DTOs**: RequestDTO para auditoría

### Infrastructure Layer
- **Messaging**: RabbitMQ client para publicar logs
- **HTTP**: Cliente HTTP para comunicación con Auth Service
- **Config**: Variables de entorno

### Presentation Layer
- **Middleware**: GatewayMiddleware (validación y auditoría)
- **Schemas**: Validación Pydantic
- **Routes**: Rutas públicas y proxy

## Flujo de Middleware

### 1. Request Entrante
```
Crea correlation_id único
   ↓
Verifica si ruta excluida (public)
   ↓
Si public: continúa sin validación
Si protected: valida token
```

### 2. Validación de Token
```
Extrae header Authorization
   ↓
Valida formato "Bearer xxxxxxx"
   ↓
Extrae token
   ↓
Consulta Auth Service
   ↓
Guarda resultado en request.state
```

### 3. Auditoría
```
Después de procesar petición
   ↓
Registra en RabbitMQ:
  - correlation_id
  - token (primeros 10 caracteres)
  - servicio destino
  - método HTTP
  - ruta
  - status code
  - timestamp
```

## Rutas Excluidas de Validación

Las siguientes rutas NO requieren token:

```
GET /health           → Health check
GET /docs             → Documentación Swagger
GET /openapi.json     → OpenAPI spec
```

## Almacenamiento de Estado en Request

```
request.state.correlation_id  → UUID único de la petición
request.state.company_id      → ID de empresa (obtenida del token)
request.state.token           → Token enviado (primeros 10 caracteres en logs)
```

## Flujo de Comunicación Asíncrona

### RabbitMQ

- **Cola**: `logs`
- **Mensaje**: 
  ```json
  {
    "service": "api-gateway",
    "level": "info|error|warning|debug",
    "message": "Descripción del evento"
  }
  ```

Eventos publicados:
- Token validado correctamente
- Token inválido
- Acceso denegado (sin token)
- Petición ruteada exitosamente
- Errores de validación

## Comunicación HTTP con Auth Service

### Validación de Token

**Petición interna**:
```
POST /auth/tokens/validate
Content-Type: application/json

{
  "token": "abc123xyz..."
}
```

**Respuesta**:
```json
{
  "valid": true,
  "company_id": 1
}
```

Timeout: 10 segundos

## Seguridad

- Requiere Bearer token en todas las peticiones protegidas
- Valida token en tiempo real contra Auth Service
- Crea correlation_id para auditoría
- Publica intentos fallidos de acceso
- Descartar tokens vacíos o malformados

## Escalabilidad

- Stateless: no mantiene estado
- HTTP client async para no bloquear
- Middleware intercepta antes de llegar a rutas
- Loguea eventos para auditoría sin bloquear
- Puede tener múltiples instancias sin conflicto

## Manejo de Errores

| Situación | Código | Respuesta |
|-----------|--------|-----------|
| Sin token | 401 | Token requerido |
| Token inválido | 401 | Token inválido |
| Auth Service inaccesible | 500 | Error interno |
| Ruta no encontrada | 404 | No encontrado |
| Error interno | 500 | Error interno |

## Flujo de Reintentos

Si Auth Service no responde:
- Timeout: 10 segundos
- Sin reintentos automáticos
- Responde 500 al cliente
- Publica log de error crítico

## Futuras Extensiones

- Caché local de validaciones por N segundos
- Rate limiting por token
- Circuit breaker para Auth Service
- Redireccionamiento a servicios internos según ruta
- Request/Response logging detallado