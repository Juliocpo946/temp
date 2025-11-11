# API Gateway - Endpoints

## URL Base
```
http://localhost:3000
```

## Endpoints Públicos (Sin Token)

### 1. Health Check

**Endpoint**
```
GET /health
```

**Descripción**
Verifica que el Gateway está funcionando correctamente.

**Response (200)**
```json
{
  "status": "ok",
  "service": "api-gateway"
}
```

---

### 2. Documentación Swagger

**Endpoint**
```
GET /docs
```

**Descripción**
Accede a la documentación interactiva Swagger UI del Gateway.

**Response**
HTML con interfaz Swagger

---

### 3. OpenAPI Specification

**Endpoint**
```
GET /openapi.json
```

**Descripción**
Obtiene la especificación OpenAPI completa del Gateway.

**Response (200)**
```json
{
  "openapi": "3.0.0",
  "info": {...},
  "paths": {...}
}
```

---

## Endpoints Protegidos (Requieren Token)

### Requisito: Authorization Header

Todas las peticiones protegidas deben incluir:

```
Authorization: Bearer <token>
```

Ejemplo:
```bash
curl -X POST http://localhost:3000/proxy/upload \
  -H "Authorization: Bearer abc123xyz456..."
```

---

### 1. Proxy de Peticiones

**Endpoint**
```
POST /proxy/{path:path}
```

**Descripción**
Rutea peticiones a servicios internos después de validar token.

**Parameters**
- `path` (path, required): Ruta del servicio interno
- `Authorization` (header, required): Bearer token

**Request**
```json
{
  "datos": "específicos del servicio"
}
```

**Response (200)**
```json
{
  "message": "Solicitud ruteada",
  "path": "ruta/especifica",
  "company_id": 1,
  "correlation_id": "uuid-1234-5678-9012"
}
```

**Errores**
- `401`: Token requerido, token inválido
- `404`: Ruta no encontrada
- `500`: Error interno

---

## Headers Especiales

### Request Headers

| Header | Requerido | Descripción |
|--------|-----------|------------|
| Authorization | Sí (excepto public) | Bearer token formato: `Bearer <token>` |
| Content-Type | No | Generalmente `application/json` |
| User-Agent | No | Identificador del cliente |

### Response Headers

| Header | Descripción |
|--------|------------|
| X-Correlation-ID | ID único de la petición para auditoría |
| Content-Type | Siempre `application/json` |

---

## Flujo de Validación de Token

### 1. Validación en Gateway

```
Cliente envía: Authorization: Bearer abc123xyz
   ↓
Gateway valida formato
   ↓
Extrae token: abc123xyz
   ↓
Valida que no esté vacío
   ↓
Si inválido: responde 401
Si válido: continúa
```

### 2. Consulta a Auth Service

```
Gateway → POST /auth/tokens/validate
   ↓
Auth Service verifica en MySQL
   ↓
Responde { valid: true, company_id: 1 }
   ↓
Gateway permite acceso
   ↓
Adiciona company_id a request.state
```

### 3. Auditoría

```
Registra en RabbitMQ:
{
  "service": "api-gateway",
  "level": "info",
  "message": "Petición ruteada: POST /ruta [200]"
}
```

---

## Códigos de Status

| Status | Significado | Ejemplo |
|--------|-----------|---------|
| 200 | Éxito | Petición procesada |
| 401 | No autorizado | Token faltante o inválido |
| 404 | No encontrado | Ruta no existe |
| 500 | Error interno | Fallo del servidor |

---

## Errores Comunes

### Error 401: Token Requerido

```json
{
  "detail": "Token requerido"
}
```

**Causa**: No incluiste header `Authorization`

**Solución**:
```bash
curl -H "Authorization: Bearer tu_token" ...
```

---

### Error 401: Token Inválido

```json
{
  "detail": "Token inválido"
}
```

**Causa**: Token no existe o está expirado

**Solución**: Genera un nuevo token en Auth Service

---

### Error 500: Auth Service Inaccesible

```json
{
  "detail": "Error interno del servidor"
}
```

**Causa**: Auth Service no responde

**Solución**: Verifica que Auth Service está levantado

---

## Ejemplo de Flujo Completo

```bash
# 1. Verificar que Gateway está activo
curl http://localhost:3000/health

# Respuesta: {"status":"ok","service":"api-gateway"}

# 2. Obtener token de Auth Service
curl -X POST http://localhost:3001/auth/companies/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Mi Empresa","email":"empresa@example.com"}'

# Respuesta: { "company": {...}, "token": "abc123xyz..." }

# 3. Usar token para acceder al Gateway
curl -X POST http://localhost:3000/proxy/upload \
  -H "Authorization: Bearer abc123xyz..." \
  -H "Content-Type: application/json" \
  -d '{"archivo":"datos"}'

# Respuesta: {"message":"Solicitud ruteada","path":"upload","company_id":1}

# 4. Intentar acceso sin token (falla)
curl -X POST http://localhost:3000/proxy/upload

# Respuesta: {"detail":"Token requerido"} [401]
```

---

## Rate Limiting (Futuro)

Actualmente no hay rate limiting. Futuras versiones pueden implementar:

- Límite de peticiones por token
- Límite de peticiones por IP
- Backoff exponencial para reintentos
- Circuit breaker si Auth Service falla

---

## Monitoreo y Auditoría

Todos los eventos se publican en RabbitMQ cola `logs`:

```json
{
  "service": "api-gateway",
  "level": "info|error|warning",
  "message": "Descripción del evento"
}
```

Estos logs pueden ser consultados en Log Service:
```
GET http://localhost:3002/logs?service=api-gateway&level=error
```