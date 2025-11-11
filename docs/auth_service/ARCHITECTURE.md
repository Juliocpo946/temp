# Auth Service - Arquitectura y Flujo

## Descripción General

El Auth Service es responsable de gestionar la autenticación y autorización de empresas. Permite el registro de nuevas empresas, generación de tokens y validación de los mismos. Utiliza MySQL para persistencia y RabbitMQ para publicar logs.

## Flujo de Negocio

### 1. Registro de Empresa

```
Cliente
   ↓
POST /auth/companies/register { name, email }
   ↓
Auth Service valida datos
   ↓
Crea empresa en MySQL
   ↓
Genera token aleatorio
   ↓
Devuelve empresa + token al cliente
   ↓
Publica log en RabbitMQ → Log Service
```

### 2. Validación de Token

```
Gateway recibe petición con token
   ↓
Consulta Auth Service vía HTTP
   ↓
Auth Service busca token en MySQL
   ↓
Valida: existe, activo, empresa activa
   ↓
Actualiza last_used
   ↓
Devuelve { valid: true, company_id }
   ↓
Gateway permite acceso a otros servicios
```

### 3. Generación de Nuevo Token

```
Cliente solicita nuevo token
   ↓
POST /auth/tokens/generate { company_id }
   ↓
Auth Service valida empresa existe y está activa
   ↓
Genera nuevo token aleatorio
   ↓
Guarda en MySQL
   ↓
Devuelve token al cliente
```

## Arquitectura por Capas

### Domain Layer
- **Entities**: Company, Token
- **Value Objects**: TokenValue (genera tokens aleatorios)
- **Repositories**: Interfaces para acceso a datos

### Application Layer
- **Use Cases**: 
  - RegisterCompany
  - ValidateToken
  - GenerateToken
  - RevokeToken
  - GetCompany
  - UpdateCompany
- **DTOs**: CompanyDTO, TokenDTO

### Infrastructure Layer
- **Persistence**:
  - Models: CompanyModel, TokenModel (ORM SQLAlchemy)
  - Repositories: Implementación de acceso a MySQL
  - Database: Configuración de conexión
- **Messaging**: RabbitMQ client para logs
- **Config**: Variables de entorno

### Presentation Layer
- **Schemas**: Validación Pydantic (CompanyCreateSchema, TokenGenerateSchema)
- **Controllers**: Lógica de endpoints
- **Routes**: Definición de rutas

## Almacenamiento de Datos

### Base de Datos: MySQL

#### Tabla: companies
- `id` (PK, INT): Identificador único
- `name` (VARCHAR): Nombre de empresa
- `email` (VARCHAR, UNIQUE): Email único
- `is_active` (BOOLEAN): Estado de empresa
- `created_at` (DATETIME): Fecha creación
- `updated_at` (DATETIME): Última actualización

#### Tabla: tokens
- `id` (PK, INT): Identificador único
- `token` (VARCHAR, UNIQUE): Token aleatorio
- `company_id` (FK): Referencia a empresa
- `created_at` (DATETIME): Fecha generación
- `expires_at` (DATETIME, NULL): Expiración opcional
- `last_used` (DATETIME, NULL): Último uso
- `is_active` (BOOLEAN): Estado del token

## Flujo de Mensajería

### RabbitMQ

- **Cola**: `logs`
- **Mensaje**: 
  ```json
  {
    "service": "auth-service",
    "level": "info|error|warning|debug",
    "message": "Descripción del evento"
  }
  ```

Eventos publicados:
- Empresa registrada exitosamente
- Intento de registro con email duplicado
- Token generado
- Token revocado
- Token validado
- Errores críticos

## Seguridad

- Tokens son strings aleatorios de 32 caracteres (base64)
- No se guardan en texto plano (aunque podrían hashearse)
- Validación de empresa activa antes de permitir token
- Revocación inmediata de tokens posible
- Auditoría vía logs en RabbitMQ

## Escalabilidad

- Stateless: cada request es independiente
- MySQL con índices en email y token para búsquedas rápidas
- Cacheble: validación de token podría cachearse en Gateway
- Desacoplado vía RabbitMQ: no bloquea por logs

## Flujo de Errores

| Situación | Código | Respuesta |
|-----------|--------|-----------|
| Email duplicado | 400 | Error: Email ya está registrado |
| Empresa no existe | 404 | Error: Empresa no existe |
| Token inválido | 401 | Error: Token inválido |
| Empresa inactiva | 400 | Error: Empresa inactiva |
| Error interno | 500 | Error interno del servidor |