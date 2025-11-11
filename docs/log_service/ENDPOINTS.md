# Log Service - Endpoints

## URL Base
```
http://localhost:3002
```

## Endpoints Públicos (Sin Token)

### 1. Health Check

**Endpoint**
```
GET /health
```

**Descripción**
Verifica que el Log Service está funcionando correctamente.

**Response (200)**
```json
{
  "status": "ok",
  "service": "log-service"
}
```

---

## Endpoints de Consulta de Logs

### 1. Obtener Todos los Logs

**Endpoint**
```
GET /logs/
```

**Descripción**
Obtiene los logs más recientes del sistema, opcionalmente filtrados.

**Query Parameters**

| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|------------|
| service | string | No | - | Filtrar por nombre de servicio |
| level | string | No | - | Filtrar por nivel (info, error, warning, debug) |
| limit | integer | No | 100 | Cantidad de logs (1-1000) |

**Request**
```
GET /logs/?service=auth-service&level=error&limit=50
```

**Response (200)**
```json
{
  "logs": [
    {
      "id": "507f1f77bcf86cd799439011",
      "service": "auth-service",
      "level": "error",
      "message": "Intento de registro con email duplicado",
      "timestamp": "2024-11-10T10:30:45.123456"
    },
    {
      "id": "507f1f77bcf86cd799439012",
      "service": "auth-service",
      "level": "error",
      "message": "Token inválido",
      "timestamp": "2024-11-10T10:25:30.987654"
    }
  ],
  "total": 2
}
```

**Errores**
- `500`: Error interno

---

### 2. Obtener Logs de un Servicio

**Endpoint**
```
GET /logs/{service}
```

**Descripción**
Obtiene todos los logs de un servicio específico.

**Parameters**
- `service` (path, required): Nombre del servicio (auth-service, api-gateway, log-service)
- `limit` (query, optional): Cantidad máxima de logs (default: 100)

**Request**
```
GET /logs/auth-service?limit=50
```

**Response (200)**
```json
{
  "logs": [
    {
      "id": "507f1f77bcf86cd799439011",
      "service": "auth-service",
      "level": "info",
      "message": "Empresa registrada",
      "timestamp": "2024-11-10T10:30:45.123456"
    },
    {
      "id": "507f1f77bcf86cd799439012",
      "service": "auth-service",
      "level": "error",
      "message": "Intento de registro con email duplicado",
      "timestamp": "2024-11-10T10:25:30.987654"
    }
  ],
  "total": 2
}
```

**Errores**
- `500`: Error interno

---

### 3. Crear Log Manualmente

**Endpoint**
```
POST /logs/
```

**Descripción**
Crea un log manualmente (útil para testing o integración externa).

**Request**
```json
{
  "service": "custom-service",
  "level": "info",
  "message": "Evento personalizado"
}
```

**Response (201)**
```json
{
  "id": "507f1f77bcf86cd799439013",
  "service": "custom-service",
  "level": "info",
  "message": "Evento personalizado",
  "timestamp": "2024-11-10T10:35:20.123456"
}
```

**Validación**
- `service` (required): String no vacío
- `level` (required): Uno de: info, error, warning, debug
- `message` (required): String no vacío

**Errores**
- `400`: Datos inválidos o nivel no reconocido
- `500`: Error interno

---

## Filtros Disponibles

### Por Servicio

Servicios conocidos:
- `auth-service` - Auth Service
- `api-gateway` - API Gateway
- `log-service` - Log Service

**Ejemplo**:
```
GET /logs/?service=auth-service
```

### Por Nivel

Niveles válidos:
- `info` - Eventos normales exitosos
- `error` - Errores críticos
- `warning` - Advertencias
- `debug` - Información de depuración

**Ejemplo**:
```
GET /logs/?level=error
```

### Combinados

```
GET /logs/?service=auth-service&level=error
```

---

## Paginación y Límites

### Parámetro limit

- Mínimo: 1
- Máximo: 1000
- Default: 100

**Ejemplo**:
```
GET /logs/?limit=500
```

### Ordenamiento

Los logs siempre se retornan ordenados por timestamp descendente (más recientes primero).

---

## Códigos de Status

| Status | Significado |
|--------|-----------|
| 200 | Consulta exitosa |
| 201 | Log creado |
| 400 | Datos inválidos |
| 500 | Error interno |

---

## Ejemplos de Uso

### Consultar últimos errores del Auth Service

```bash
curl "http://localhost:3002/logs/?service=auth-service&level=error&limit=10"
```

**Respuesta**:
```json
{
  "logs": [
    {
      "id": "507f1f77bcf86cd799439011",
      "service": "auth-service",
      "level": "error",
      "message": "Intento de validación con token inexistente",
      "timestamp": "2024-11-10T10:30:45.123456"
    }
  ],
  "total": 1
}
```

---

### Consultar todos los errores del sistema

```bash
curl "http://localhost:3002/logs/?level=error"
```

**Respuesta**:
```json
{
  "logs": [
    {
      "id": "507f1f77bcf86cd799439011",
      "service": "auth-service",
      "level": "error",
      "message": "Email duplicado",
      "timestamp": "2024-11-10T10:30:45.123456"
    },
    {
      "id": "507f1f77bcf86cd799439012",
      "service": "api-gateway",
      "level": "error",
      "message": "Token inválido",
      "timestamp": "2024-11-10T10:25:30.987654"
    }
  ],
  "total": 2
}
```

---

### Consultar logs del API Gateway

```bash
curl "http://localhost:3002/logs/api-gateway?limit=20"
```

**Respuesta**:
```json
{
  "logs": [
    {
      "id": "507f1f77bcf86cd799439012",
      "service": "api-gateway",
      "level": "info",
      "message": "Token validado correctamente",
      "timestamp": "2024-11-10T10:25:30.987654"
    },
    {
      "id": "507f1f77bcf86cd799439013",
      "service": "api-gateway",
      "level": "error",
      "message": "Acceso denegado: falta token",
      "timestamp": "2024-11-10T10:20:15.654321"
    }
  ],
  "total": 2
}
```

---

### Crear un log manual

```bash
curl -X POST http://localhost:3002/logs/ \
  -H "Content-Type: application/json" \
  -d '{
    "service": "test-service",
    "level": "info",
    "message": "Prueba de log manual"
  }'
```

**Respuesta**:
```json
{
  "id": "507f1f77bcf86cd799439014",
  "service": "test-service",
  "level": "info",
  "message": "Prueba de log manual",
  "timestamp": "2024-11-10T10:40:00.123456"
}
```

---

### Error: Nivel no válido

```bash
curl -X POST http://localhost:3002/logs/ \
  -H "Content-Type: application/json" \
  -d '{
    "service": "test-service",
    "level": "invalid",
    "message": "Prueba"
  }'
```

**Respuesta (400)**:
```json
{
  "detail": "Nivel de log inválido: invalid"
}
```

---

## Monitoreo

Los logs se publican automáticamente desde:

- **Auth Service**: Registros de empresa, token, errores
- **API Gateway**: Validaciones, accesos denegados
- **Log Service**: Consumo de cola

Todos con timestamp automático en UTC.

---

## Retención de Logs

Actualmente: Sin límite de retención

Futuras opciones:
- TTL automático (ej: 30 días)
- Archivado a almacenamiento frío
- Compresión de logs antiguos