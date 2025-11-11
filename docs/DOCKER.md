# Guía de Mantenimiento y Troubleshooting - Microservicios

## Verificar Variables de Entorno

### Verificar variables en un contenedor específico

```bash
# Ver TODAS las variables de entorno del contenedor
docker-compose exec auth_service env

# Ver solo variables específicas
docker-compose exec auth_service env | grep MYSQL
docker-compose exec auth_service env | grep AMQP

# Verificar que .env se está cargando
docker-compose exec log_service env | grep MONGO
docker-compose exec api_gateway env | grep AUTH_SERVICE
```

### Verificar que el servicio puede acceder a las credenciales

```bash
# Conectar a un contenedor y verificar
docker-compose exec auth_service python -c "from src.infrastructure.config.settings import MYSQL_HOST, AMQP_URL; print(f'MySQL: {MYSQL_HOST}'); print(f'AMQP URL cargada: {bool(AMQP_URL)}')"
```

---

## Chequear Errores Comunes

### Error: Can't connect to MySQL

```bash
# 1. Ver logs del servicio
docker-compose logs auth_service

# 2. Verificar que MySQL está corriendo
mysql -u root -p -e "SELECT 1;"

# 3. Verificar variable MYSQL_HOST en contenedor
docker-compose exec auth_service env | grep MYSQL_HOST

# 4. Probar conexión desde dentro del contenedor
docker-compose exec auth_service python -c "import pymysql; pymysql.connect(host='host.docker.internal', user='root', password='123456')"
```

### Error: Can't connect to RabbitMQ/AMQP

```bash
# 1. Ver logs
docker-compose logs <servicio>

# 2. Verificar AMQP_URL
docker-compose exec <servicio> env | grep AMQP_URL

# 3. Verificar que CloudAMQP URL es válida
docker-compose exec <servicio> python -c "from src.infrastructure.config.settings import AMQP_URL; print(AMQP_URL)"
```

### Error: Can't connect to MongoDB

```bash
# 1. Ver logs
docker-compose logs log_service

# 2. Verificar MONGO_URL
docker-compose exec log_service env | grep MONGO_URL

# 3. Verificar credenciales de MongoDB Atlas
docker-compose exec log_service python -c "from src.infrastructure.config.settings import MONGO_URL; print(MONGO_URL[:50] + '...')"
```

### Error: DeprecationWarning en logs

Significa que el código del contenedor es viejo. Necesitas reconstruir:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Ver Logs Detallados

### Ver logs de todos los servicios

```bash
# Todos los logs
docker-compose logs

# Últimas 100 líneas
docker-compose logs --tail=100

# En tiempo real (follow)
docker-compose logs -f
```

### Ver logs de un servicio específico

```bash
# Auth Service
docker-compose logs -f auth_service

# API Gateway
docker-compose logs -f api_gateway

# Log Service
docker-compose logs -f log_service
```

### Filtrar logs

```bash
# Ver solo errores
docker-compose logs | grep -i error

# Ver solo warnings
docker-compose logs | grep -i warning

# Ver último minuto
docker-compose logs --since 1m
```

---

## Limpiar Contenedores y Volúmenes

### Opción 1: Detener servicios sin limpiar (datos persisten)

```bash
docker-compose stop
```

Contenedores se detienen pero NO se elimina nada. Puedes hacer `docker-compose up -d` para reanudar.

### Opción 2: Detener y eliminar contenedores (datos persisten)

```bash
docker-compose down
```

Elimina contenedores pero mantiene volúmenes (datos en BD).

### Opción 3: Limpiar TODO (volúmenes también se eliminan)

```bash
# Opción 3a: Eliminar solo este servicio
cd auth-service
docker-compose down -v

# Opción 3b: Desde padre, especificar archivo
docker-compose -f auth-service/docker-compose.yml down -v
```

ADVERTENCIA: Esto elimina datos de MongoDB y MySQL almacenados en volúmenes.

### Opción 4: Limpiar imágenes y todo

```bash
# Eliminar contenedores, volúmenes E imágenes
docker-compose down -v --rmi all

# -v: elimina volúmenes
# --rmi all: elimina todas las imágenes relacionadas
```

---

## Reconstruir Servicios Correctamente

### Cuando cambias código Python

```bash
cd auth-service

# Paso 1: Detener
docker-compose down

# Paso 2: Reconstruir (IMPORTANTE)
docker-compose build --no-cache

# Paso 3: Levantar
docker-compose up -d

# Paso 4: Verificar
docker-compose logs -f
```

El `--no-cache` es crucial porque sin él Docker usa capas guardadas.

### Cuando cambias requirements.txt

```bash
cd log-service

# 1. Detener
docker-compose down

# 2. Reconstruir
docker-compose build --no-cache

# 3. Levantar
docker-compose up -d
```

### Cuando cambias .env

```bash
# Solo necesitas reiniciar (sin rebuild)
docker-compose restart
```

---

## Verificar Estado de Servicios

### Ver contenedores corriendo

```bash
docker ps
```

Muestra:
- CONTAINER ID
- IMAGE
- STATUS (Up X minutes)
- PORTS

### Ver todos los contenedores (incluyendo detenidos)

```bash
docker ps -a
```

### Ver información detallada de un contenedor

```bash
docker inspect auth_service-1
```

### Verificar health checks

```bash
curl http://localhost:3001/health
curl http://localhost:3000/health
curl http://localhost:3002/health
```

Respuesta esperada:
```json
{"status":"ok","service":"auth-service"}
```

---

## Flujo Completo de Troubleshooting

### Paso 1: Verificar que Docker está corriendo

```bash
docker ps
```

Si no sale nada o error, inicia Docker Desktop (Windows/Mac).

### Paso 2: Ver logs de error

```bash
docker-compose logs
```

Identifica el error exacto.

### Paso 3: Según el error

**Error de conexión a BD:**
- Verifica que la BD existe
- Verifica credenciales en .env
- Verifica que el host es accesible

**Error de variable no definida:**
- Verifica que .env existe en la carpeta
- Verifica que docker-compose.yml tiene `env_file: - .env`
- Reconstruye: `docker-compose build --no-cache`

**Error de deprecated code:**
- Reconstruye: `docker-compose build --no-cache`

### Paso 4: Reintentar

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f
```

---

## Levantar Servicios en Orden Correcto

### Orden de levantamiento

```bash
# 1. Auth Service
cd auth-service
docker-compose up -d
sleep 3

# 2. Log Service
cd ../log-service
docker-compose up -d
sleep 3

# 3. API Gateway
cd ../api-gateway
docker-compose up -d

# Verificar
docker ps
```

### Script automatizado

```bash
#!/bin/bash

echo "Levantando Auth Service..."
cd auth-service && docker-compose up -d && cd ..
sleep 3

echo "Levantando Log Service..."
cd log-service && docker-compose up -d && cd ..
sleep 3

echo "Levantando API Gateway..."
cd api-gateway && docker-compose up -d && cd ..

echo "Servicios levantados"
sleep 2

echo "Health checks:"
curl http://localhost:3001/health
curl http://localhost:3002/health
curl http://localhost:3000/health
```

---

## Reiniciar Un Servicio

### Reiniciar sin rebuild (si solo cambió .env)

```bash
docker-compose restart auth_service
```

### Rebuild y reiniciar (si cambió código)

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Detener Servicios

### Detener solo uno

```bash
cd auth-service
docker-compose stop
# o
docker-compose down
```

### Detener todos desde carpetas diferentes

```bash
docker-compose -f auth-service/docker-compose.yml down
docker-compose -f log-service/docker-compose.yml down
docker-compose -f api-gateway/docker-compose.yml down
```

### Script para detener todo

```bash
#!/bin/bash

echo "Deteniendo Auth Service..."
cd auth-service && docker-compose down && cd ..

echo "Deteniendo Log Service..."
cd log-service && docker-compose down && cd ..

echo "Deteniendo API Gateway..."
cd api-gateway && docker-compose down && cd ..

echo "Todos los servicios detenidos"
```

---

## Checklist de Antes de Empezar

- [ ] MySQL está corriendo en localhost:3306
- [ ] MongoDB Atlas es accesible
- [ ] CloudAMQP es accesible (prueba conexión)
- [ ] .env existe en cada carpeta de servicio
- [ ] docker-compose.yml existe en cada carpeta
- [ ] Dockerfile existe en cada carpeta
- [ ] requirements.txt existe en cada carpeta
- [ ] Docker Desktop está corriendo

---

## Comandos Rápidos de Referencia

```bash
# Ver contenedores
docker ps
docker ps -a

# Ver logs
docker-compose logs
docker-compose logs -f
docker-compose logs -f auth_service

# Reconstruir
docker-compose build --no-cache

# Levantar
docker-compose up -d

# Detener
docker-compose down

# Limpiar todo
docker-compose down -v --rmi all

# Verificar variables
docker-compose exec auth_service env | grep MYSQL

# Health check
curl http://localhost:3001/health

# Reiniciar
docker-compose restart
```