# Auth Service - Endpoints

## URL Base
```
http://localhost:3001
```

## Endpoints de Empresa

### 1. Registrar Empresa

**Endpoint**
```
POST /auth/companies/register
```

**Descripción**
Registra una nueva empresa y devuelve un token inicial para usarlo en todas las peticiones posteriores.

**Request**
```json
{
  "name": "Mi Empresa",
  "email": "empresa@example.com"
}
```

**Response (201)**
```json
{
  "company": {
    "id": 1,
    "name": "Mi Empresa",
    "email": "empresa@example.com",
    "is_active": true,
    "created_at": "2024-11-10T10:30:00",
    "updated_at": "2024-11-10T10:30:00"
  },
  "token": "abc123xyz456..."
}
```

**Errores**
- `400`: Email ya está registrado
- `500`: Error interno

---

### 2. Obtener Empresa

**Endpoint**
```
GET /auth/companies/{company_id}
```

**Descripción**
Obtiene información de una empresa específica.

**Parameters**
- `company_id` (path, required): ID de la empresa

**Response (200)**
```json
{
  "id": 1,
  "name": "Mi Empresa",
  "email": "empresa@example.com",
  "is_active": true,
  "created_at": "2024-11-10T10:30:00",
  "updated_at": "2024-11-10T10:30:00"
}
```

**Errores**
- `404`: Empresa no existe
- `500`: Error interno

---

### 3. Actualizar Empresa

**Endpoint**
```
PUT /auth/companies/{company_id}
```

**Descripción**
Actualiza datos de una empresa (nombre, email, estado).

**Parameters**
- `company_id` (path, required): ID de la empresa

**Request** (todos los campos opcionales)
```json
{
  "name": "Nuevo Nombre",
  "email": "nuevoemail@example.com",
  "is_active": false
}
```

**Response (200)**
```json
{
  "id": 1,
  "name": "Nuevo Nombre",
  "email": "nuevoemail@example.com",
  "is_active": false,
  "created_at": "2024-11-10T10:30:00",
  "updated_at": "2024-11-10T10:45:00"
}
```

**Errores**
- `400`: Email ya en uso o datos inválidos
- `404`: Empresa no existe
- `500`: Error interno

---

## Endpoints de Token

### 1. Generar Token

**Endpoint**
```
POST /auth/tokens/generate
```

**Descripción**
Genera un nuevo token para una empresa existente. Útil cuando necesitas un nuevo token o el actual fue comprometido.

**Request**
```json
{
  "company_id": 1
}
```

**Response (200)**
```json
{
  "token": "nuevo_token_aleatorio_xyz..."
}
```

**Errores**
- `400`: Empresa no existe o está inactiva
- `500`: Error interno

---

### 2. Validar Token

**Endpoint**
```
POST /auth/tokens/validate
```

**Descripción**
Valida un token y devuelve información de la empresa asociada. Usado internamente por API Gateway.

**Request**
```json
{
  "token": "abc123xyz456..."
}
```

**Response (200)**
```json
{
  "valid": true,
  "company_id": 1
}
```

O en caso de token inválido:
```json
{
  "valid": false,
  "company_id": null
}
```

**Errores**
- `500`: Error interno

---

### 3. Revocar Token

**Endpoint**
```
POST /auth/tokens/revoke
```

**Descripción**
Invalida un token específico. Después de revocar, el token no podrá usarse más.

**Request**
```json
{
  "token": "abc123xyz456..."
}
```

**Response (200)**
```json
{
  "success": true
}
```

**Errores**
- `404`: Token no existe
- `500`: Error interno

---

## Endpoint de Health Check

### Health Check

**Endpoint**
```
GET /health
```

**Descripción**
Verifica que el servicio está funcionando correctamente.

**Response (200)**
```json
{
  "status": "ok",
  "service": "auth-service"
}
```

---

## Validación de Datos

### Company Create
- `name` (string, required): 1-255 caracteres
- `email` (string, required): Email válido, único

### Company Update
- `name` (string, optional): 1-255 caracteres
- `email` (string, optional): Email válido, único
- `is_active` (boolean, optional): true o false

### Token Generate
- `company_id` (integer, required): ID válido de empresa existente

### Token Revoke
- `token` (string, required): Token válido y existente

---

## Códigos de Status

| Status | Significado |
|--------|------------|
| 200 | Operación exitosa |
| 201 | Recurso creado |
| 400 | Solicitud inválida |
| 404 | Recurso no encontrado |
| 500 | Error interno del servidor |

---

## Ejemplo de Flujo Completo

```bash
# 1. Registrar empresa
curl -X POST http://localhost:3001/auth/companies/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Mi Empresa","email":"empresa@example.com"}'

# Respuesta: { "company": {...}, "token": "abc123..." }

# 2. Usar token para acceder al Gateway
curl -X POST http://localhost:3000/proxy/upload \
  -H "Authorization: Bearer abc123..."

# 3. Generar nuevo token si es necesario
curl -X POST http://localhost:3001/auth/tokens/generate \
  -H "Content-Type: application/json" \
  -d '{"company_id":1}'

# 4. Revocar token antiguo
curl -X POST http://localhost:3001/auth/tokens/revoke \
  -H "Content-Type: application/json" \
  -d '{"token":"abc123..."}'
```