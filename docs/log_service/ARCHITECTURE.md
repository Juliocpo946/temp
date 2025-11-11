# Log Service - Arquitectura y Flujo

## Descripción General

El Log Service centraliza todos los logs del sistema. Consume eventos de RabbitMQ desde otros servicios y los almacena en MongoDB. Proporciona endpoints para consultar logs por servicio, nivel o ambos. No requiere tokens para consultar (pero podrían agregarse).

## Flujo de Negocio

### 1. Recepción de Log desde RabbitMQ

```
Servicio (Auth, Gateway) publica log
   ↓
RabbitMQ cola "logs" recibe mensaje
   ↓
Log Service consume de la cola (background thread)
   ↓
Extrae: service, level, message
   ↓
Crea documento Log
   ↓
Guarda en MongoDB
   ↓
Acknowledge mensaje en RabbitMQ
   ↓
Si error: requeue mensaje
```

### 2. Consulta de Logs

```
Cliente solicita logs
   ↓
GET /logs/?service=auth-service&level=error
   ↓
Log Service consulta MongoDB
   ↓
Filtra por servicio y nivel
   ↓
Ordena por timestamp descendente
   ↓
Devuelve últimos N logs
```

### 3. Consumo Asíncrono

```
Log Service inicia
   ↓
Crea thread daemon
   ↓
Se conecta a RabbitMQ
   ↓
Comienza a escuchar cola "logs"
   ↓
Procesa mensajes en background
   ↓
Nunca bloquea el servidor HTTP
```

## Arquitectura por Capas

### Domain Layer
- **Entities**: Log
- **Value Objects**: LogLevel (enum: info, error, warning, debug)
- **Repositories**: Interfaz para acceso a datos

### Application Layer
- **Use Cases**:
  - SaveLog: Guarda un log en base de datos
  - GetLogs: Consulta logs con filtros
- **DTOs**: LogDTO para serialización

### Infrastructure Layer
- **Persistence**:
  - Models: LogModel (ODM MongoEngine)
  - Repositories: Implementación de acceso a MongoDB
  - Database: Configuración de conexión
- **Messaging**:
  - RabbitMQ client para consumir
  - LogConsumer para procesamiento asíncrono
- **Config**: Variables de entorno

### Presentation Layer
- **Schemas**: Validación Pydantic (LogCreateSchema, LogsQuerySchema)
- **Controllers**: Lógica de endpoints
- **Routes**: Definición de rutas

## Almacenamiento de Datos

### Base de Datos: MongoDB

#### Colección: logs

Documento:
```json
{
  "_id": ObjectId("..."),
  "service": "auth-service",
  "level": "error",
  "message": "Error al registrar empresa",
  "timestamp": ISODate("2024-11-10T10:30:45.123Z")
}
```

**Índices**:
- `timestamp` (descendente): Búsquedas rápidas por fecha
- `service`: Filtrar por servicio
- `level`: Filtrar por nivel

**Retención**: Sin límite (pero podría implementarse TTL)

## Flujo de Mensajería

### RabbitMQ Consumer

```
Conexión a RabbitMQ (localhost:5672)
   ↓
Declara cola "logs" con durability=true
   ↓
Comienza a consumir mensajes
   ↓
Por cada mensaje:
  1. Parsea JSON
  2. Crea Log entity
  3. Guarda en MongoDB
  4. Acknowledge (confirma procesamiento)
   ↓
Si error: Nack + Requeue (reintentar)
```

### Formato de Mensaje

Los servicios publican en cola "logs":

```json
{
  "service": "auth-service",
  "level": "info",
  "message": "Empresa registrada: empresa@example.com"
}
```

O en caso de error:

```json
{
  "service": "api-gateway",
  "level": "error",
  "message": "Token inválido"
}
```

## Thread de Consumo

```
FastAPI app inicia
   ↓
En evento @app.on_event("startup"):
  1. Conecta a MongoDB
  2. Crea LogConsumer
  3. Inicia thread daemon
   ↓
Thread daemon comienza a escuchar
   ↓
Procesa logs en background
   ↓
No interfiere con endpoints HTTP
   ↓
En evento @app.on_event("shutdown"):
  1. Desconecta MongoDB
  2. Cierra RabbitMQ
```

## Niveles de Log

| Nivel | Uso |
|-------|-----|
| `info` | Eventos exitosos (registro, token generado, etc) |
| `error` | Errores críticos (email duplicado, token inválido, etc) |
| `warning` | Situaciones atípicas (token a punto de expirar) |
| `debug` | Información de depuración (valores internos) |

## Escalabilidad

- MongoDB: Soporta millones de documentos
- Índices: Búsquedas O(log n)
- Consumer asíncrono: No bloquea
- Sin estado: Múltiples instancias posibles
- Retención: Podría implementarse TTL

## Manejo de Errores

### Error de Conexión a MongoDB

```
Al iniciar:
  - Intenta conectar
  - Si falla: Exception levantada
  - No inicia servicio
```

### Error al Procesar Mensaje

```
Durante consumo:
  - JSON inválido → Nack + Requeue
  - BD inaccesible → Nack + Requeue
  - Después de N reintentos → Deadletter queue
```

### Error de Conexión a RabbitMQ

```
Consumer thread:
  - Intenta conectar
  - Si falla: Exception en thread
  - Log en stdout
```

## Flujo de Consultas

### Obtener Todos los Logs (últimos 100)

```
GET /logs/
   ↓
Query: find() ordenado por -timestamp
   ↓
Limit: 100
   ↓
Retorna array de 100 logs más recientes
```

### Obtener Logs de un Servicio

```
GET /logs/?service=auth-service
   ↓
Query: find(service="auth-service")
   ↓
Ordenado por -timestamp
   ↓
Limit: 100 (configurable)
```

### Obtener Logs de un Nivel

```
GET /logs/?level=error
   ↓
Query: find(level="error")
   ↓
Ordenado por -timestamp
   ↓
Limit: 100
```

### Obtener Logs de Servicio Y Nivel

```
GET /logs/?service=auth-service&level=error
   ↓
Query: find(service="auth-service", level="error")
   ↓
Ordenado por -timestamp
   ↓
Limit: configurable
```

## Seguridad

- Logs públicos (sin autenticación requerida)
- Podrían protegerse con tokens en futuro
- Información sensible no se loguea (passwords, etc)
- Solo servicios internos pueden publicar en cola

## Ventajas del Diseño

- **Centralizado**: Todos los logs en un lugar
- **Asíncrono**: No bloquea otros servicios
- **Escalable**: MongoDB maneja gran volumen
- **Queryable**: Filtros flexibles
- **Auditable**: Timestamp automático en todos

## Futuras Extensiones

- Autenticación para consultar logs
- TTL automático para eliminar logs antiguos
- Alertas cuando errores superan threshold
- Exportación a ELK stack
- Grafanas dashboards
- Rate limiting en consultas