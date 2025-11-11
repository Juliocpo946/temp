# Cómo Docker Compose Lee del .env

## Configuración Actual

Cada servicio tiene un `docker-compose.yml` con:

```yaml
services:
  servicio:
    build: .
    ports:
      - "3001:3001"
    env_file:
      - .env
    networks:
      - microservices
```

## Cómo Funciona

### 1. Docker Compose Lee .env

Cuando ejecutas:
```bash
cd auth-service
docker-compose up -d
```

Docker Compose:
1. Lee el archivo `.env` en la misma carpeta
2. Carga todas las variables de entorno del `.env`
3. Las pasa como environment variables al contenedor
4. El código Python lee con `os.getenv()`

### 2. Flujo de Variables

```
.env (archivo)
  ↓
docker-compose.yml (env_file: - .env)
  ↓
Contenedor (variables de entorno)
  ↓
settings.py (lee con os.getenv())
```

### 3. Ejemplo Completo

**auth-service/.env:**
```
MYSQL_HOST=host.docker.internal
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
AMQP_URL=amqps://siptuvyg:...@gorilla.lmq.cloudamqp.com/siptuvyg
SERVICE_NAME=auth-service
SERVICE_PORT=3001
LOG_SERVICE_QUEUE=logs
```

**auth-service/docker-compose.yml:**
```yaml
env_file:
  - .env
```

**auth-service/src/infrastructure/config/settings.py:**
```python
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
AMQP_URL = os.getenv("AMQP_URL")
```

El contenedor recibe todos estos valores automáticamente.

## Ventajas

✅ No hardcodeas en docker-compose.yml
✅ Las credenciales están en .env (local, no en Git)
✅ Mismo proceso que localmente (sin Docker)
✅ Fácil cambiar entre dev/prod (distintos .env)
✅ Seguridad: .env está en .gitignore

## Con Docker vs Sin Docker

### Sin Docker (Local)
```bash
cd auth-service
python main.py
```
Lee: `.env` → `settings.py` → variables de entorno

### Con Docker
```bash
cd auth-service
docker-compose up -d
```
Lee: `.env` → `docker-compose.yml` → contenedor → `settings.py`

Mismo resultado, diferente camino.

## Múltiples .env (Dev/Prod)

Si necesitaras múltiples configuraciones:

```bash
# Development
docker-compose --env-file .env.dev up -d

# Production
docker-compose --env-file .env.prod up -d
```

O en docker-compose.yml especificar varios:

```yaml
env_file:
  - .env
  - .env.local
```

## Importante: host.docker.internal

En los `.env`:
- **Auth Service:** `MYSQL_HOST=host.docker.internal` (accede a MySQL en tu máquina)
- **API Gateway:** `AUTH_SERVICE_URL=http://host.docker.internal:3001` (accede a Auth Service en tu máquina)

Sin esto, los contenedores no pueden acceder a servicios locales.

## Verificar Variables en Contenedor

```bash
docker-compose exec auth_service env | grep MYSQL
```

Muestra todas las variables de entorno que tiene el contenedor.