# Arquitectura de Microservicios

## Estructura General

### Carpetas por Servicio

```
servicio/
├── src/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── presentation/
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .env
└── .gitignore
```

### Capas de Arquitectura Hexagonal

#### 1. **Domain (Dominio)**
- Contiene la lógica de negocio pura
- Independiente de cualquier framework
- Carpetas:
  - `entities/` - Objetos de dominio con comportamiento
  - `repositories/` - Interfaces de repositorios
  - `value_objects/` - Valores inmutables del dominio

#### 2. **Application (Aplicación)**
- Orquesta el flujo de casos de uso
- Conecta domain con infrastructure
- Carpetas:
  - `use_cases/` - Casos de uso del negocio
  - `dtos/` - Objetos de transferencia de datos

#### 3. **Infrastructure (Infraestructura)**
- Implementaciones técnicas
- Bases de datos, mensajería, configuración
- Carpetas:
  - `persistence/` - Acceso a datos (models, repositories)
  - `messaging/` - Comunicación (RabbitMQ, etc)
  - `http/` - Clientes HTTP
  - `config/` - Configuración y settings

#### 4. **Presentation (Presentación)**
- Capa de API REST
- Validación de entrada con Pydantic
- Carpetas:
  - `schemas/` - Validación Pydantic
  - `controllers/` - Lógica de endpoints
  - `middleware/` - Middleware HTTP
  - `routes/` - Definición de rutas

## Patrones Implementados

### SOLID Principles
- Single Responsibility: cada clase tiene una responsabilidad
- Open/Closed: extensible, cerrado a modificación
- Liskov Substitution: interfaces intercambiables
- Interface Segregation: interfaces específicas
- Dependency Inversion: depende de abstracciones

### Domain-Driven Design
- Entidades con identidad única
- Value Objects inmutables
- Repositorios para persistencia
- Use Cases como orquestadores

### Inyección de Dependencias
- Dependencies inyectadas en constructores
- FastAPI Depends para endpoints
- Bajo acoplamiento entre capas

## Comunicación entre Servicios

- **HTTP REST**: Para validación síncrona (Gateway ↔ Auth Service)
- **RabbitMQ**: Para mensajería asíncrona (publicación de logs)
- **Colas de trabajo**: Desacoplamiento de servicios

## Tecnologías Estándar

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Framework Web | FastAPI | 0.104.1 |
| Servidor ASGI | Uvicorn | 0.24.0 |
| Validación | Pydantic | 2.5.0 |
| ORM/ODM | SQLAlchemy / MongoEngine | 2.0.23 / 0.27.0 |
| BD Relacional | MySQL | 8.0 |
| BD NoSQL | MongoDB | 7.0 |
| Message Broker | RabbitMQ | 3.12 |
| Cliente RPC | pika | 1.3.2 |
| Cliente HTTP | httpx | 0.25.0 |
| Env Variables | python-dotenv | 1.0.0 |
| Contenedorización | Docker | Latest |
| Orquestación | Docker Compose | 3.8 |

## Principios de Codificación

- **Código limpio**: Sin líneas innecesarias
- **Altamente legible**: Funciones puras y parametrizadas
- **Sin hardcoding**: Uso de parámetros y constantes
- **Logs únicamente críticos**: Errores graves solamente
- **Sin comentarios**: Código auto-documentado
- **Idioma inglés**: Todo código en inglés
- **Mensajes en español**: Logs, prints, errores en español