# Guía de Configuración: RabbitMQ (CloudAMQP) y MQTT (HiveMQ Cloud)

Esta guía te ayudará a migrar RabbitMQ y MQTT de local a servicios en la nube **100% gratuitos**.

---

## 1. RabbitMQ - CloudAMQP (AMQP)

### Paso 1: Crear cuenta en CloudAMQP

1. Ve a https://www.cloudamqp.com/
2. Haz clic en "Sign up"
3. Puedes registrarte con:
   - Email y contraseña
   - GitHub
   - Google

### Paso 2: Crear una instancia de RabbitMQ

1. Una vez dentro del dashboard, haz clic en **"+ Create New Instance"**
2. Configura la instancia:
   - **Name**: `lsm-rabbitmq` (o el nombre que prefieras)
   - **Plan**: Selecciona **"Little Lemur (Free)"**
   - **Region**: Selecciona la más cercana (ej: `US-East-1`, `US-West-1`, o `EU-West-1`)
   - **Tags**: (opcional)
3. Haz clic en **"Create instance"**
4. Espera unos segundos mientras se crea la instancia

### Paso 3: Obtener la URL de conexión

1. En el dashboard, haz clic en tu instancia recién creada
2. En la página de detalles, encontrarás:
   - **AMQP URL**: Esta es la URL de conexión principal
   - Se verá algo así:
     ```
     amqps://user:password@shrimp.rmq.cloudamqp.com/vhost
     ```
3. **Copia esta URL completa** (la necesitarás en el siguiente paso)

### Paso 4: Información adicional disponible

En el dashboard de CloudAMQP también verás:
- **Host**: `shrimp.rmq.cloudamqp.com` (ejemplo)
- **User & Vhost**: Tu usuario y vhost
- **Password**: Tu contraseña
- **Management URL**: Para acceder a la interfaz web de RabbitMQ

### Paso 5: Actualizar archivos de configuración

Necesitas actualizar los archivos `.env` de los siguientes microservicios:

#### a) `microservices/cognitive-data-service/.env`

```env
# Base de datos (MySQL)
DB_HOST=host.docker.internal
DB_USER=root
DB_PASSWORD=123456
DB_NAME=cognitive_data_db
DB_PORT=3306

# Mensajería - RabbitMQ CloudAMQP
RABBITMQ_URL=amqps://user:password@shrimp.rmq.cloudamqp.com/vhost

# MQTT (actualizar más adelante)
MQTT_HOST=mqtt_broker
MQTT_PORT=1883

# Servicios
AUTH_SERVICE_URL=http://auth_service:8000
LOGS_SERVICE_URL=http://logs_service:8009
SESSION_SERVICE_URL=http://session_management_service:8002
```

#### b) `microservices/session-management-service/.env`

```env
# Base de datos (MySQL)
DB_HOST=host.docker.internal
DB_USER=root
DB_PASSWORD=123456
DB_NAME=session_management_db
DB_PORT=3306

# Mensajería - RabbitMQ CloudAMQP
RABBITMQ_URL=amqps://user:password@shrimp.rmq.cloudamqp.com/vhost

# MQTT (actualizar más adelante)
MQTT_HOST=mqtt_broker
MQTT_PORT=1883

# Servicios
AUTH_SERVICE_URL=http://auth_service:8000
LOGS_SERVICE_URL=http://logs_service:8009
```

#### c) `microservices/monitoring-alerts-service/.env`

```env
# Mensajería - RabbitMQ CloudAMQP
RABBITMQ_URL=amqps://user:password@shrimp.rmq.cloudamqp.com/vhost

# MQTT (actualizar más adelante)
MQTT_BROKER_HOST=mqtt_broker
MQTT_BROKER_PORT=1883

# Otros servicios y configuraciones...
```

#### d) `microservices/analytics-service/.env`

```env
# Mensajería - RabbitMQ CloudAMQP
RABBITMQ_URL=amqps://user:password@shrimp.rmq.cloudamqp.com/vhost

# Otros servicios y configuraciones...
```

### Paso 6: Actualizar docker-compose.yml

Comenta el servicio de RabbitMQ local en `docker-compose.yml`:

```yaml
  # ==========================================
  # RabbitMQ - MIGRADO A CLOUDAMQP
  # ==========================================

  # rabbitmq:
  #   image: rabbitmq:3.12-management
  #   container_name: rabbitmq
  #   environment:
  #     RABBITMQ_DEFAULT_USER: ${RABBITMQ_DEFAULT_USER}
  #     RABBITMQ_DEFAULT_PASS: ${RABBITMQ_DEFAULT_PASS}
  #   ports:
  #     - "5672:5672"
  #     - "15672:15672"
  #   volumes:
  #     - rabbitmq_data:/var/lib/rabbitmq
  #   networks:
  #     - lsm_network
  #   healthcheck:
  #     test: ["CMD", "rabbitmq-diagnostics", "ping"]
  #     interval: 10s
  #     timeout: 5s
  #     retries: 5
```

También **elimina las dependencias** de `rabbitmq` en los microservicios:

**ANTES:**
```yaml
  cognitive_data_service:
    build:
      context: ./microservices/cognitive-data-service
      dockerfile: Dockerfile
    container_name: cognitive_data_service
    env_file:
      - ./microservices/cognitive-data-service/.env
    ports:
      - "8001:8001"
    networks:
      - lsm_network
    depends_on:
      rabbitmq:                    # ← ELIMINAR ESTO
        condition: service_healthy # ← ELIMINAR ESTO
      auth_service:
        condition: service_started
      logs_service:
        condition: service_started
```

**DESPUÉS:**
```yaml
  cognitive_data_service:
    build:
      context: ./microservices/cognitive-data-service
      dockerfile: Dockerfile
    container_name: cognitive_data_service
    env_file:
      - ./microservices/cognitive-data-service/.env
    ports:
      - "8001:8001"
    networks:
      - lsm_network
    depends_on:
      auth_service:
        condition: service_started
      logs_service:
        condition: service_started
```

Repite esto para:
- `session_management_service`
- `monitoring_alerts_service`
- `analytics_service`
- `recommendations_service`

### Paso 7: Probar la conexión

1. Levanta tus servicios:
   ```bash
   docker-compose up -d
   ```

2. Verifica los logs de los servicios que usan RabbitMQ:
   ```bash
   docker logs cognitive_data_service
   docker logs session_management_service
   docker logs monitoring_alerts_service
   docker logs analytics_service
   ```

3. Si todo está correcto, deberías ver mensajes de conexión exitosa a RabbitMQ.

---

## 2. MQTT - HiveMQ Cloud

### Paso 1: Crear cuenta en HiveMQ Cloud

1. Ve a https://console.hivemq.cloud/
2. Haz clic en "Sign Up"
3. Completa el formulario de registro
4. Verifica tu email

### Paso 2: Crear un Cluster

1. Una vez dentro del dashboard, haz clic en **"Create Cluster"**
2. Configura el cluster:
   - **Cluster Name**: `lsm-mqtt-cluster` (o el nombre que prefieras)
   - **Plan**: Selecciona **"Serverless - Free"** o **"Starter - Free"**
   - **Cloud Provider**: AWS, Google Cloud, o Azure (elige el que prefieras)
   - **Region**: Selecciona la más cercana (ej: `us-east-1`)
3. Haz clic en **"Create"**
4. Espera unos minutos mientras se crea el cluster

### Paso 3: Configurar credenciales

1. Una vez creado el cluster, haz clic en él para ver los detalles
2. Ve a la pestaña **"Access Management"** o **"Credentials"**
3. Haz clic en **"Add Credentials"** o **"Create Credentials"**
4. Crea un nuevo usuario:
   - **Username**: `lsm_mqtt_user` (o el que prefieras)
   - **Password**: Genera una contraseña segura o usa la generada automáticamente
   - **Permissions**: Selecciona permisos de publicación y suscripción (Publish/Subscribe)
5. **Guarda estas credenciales** (no podrás verlas de nuevo)

### Paso 4: Obtener información de conexión

En el dashboard del cluster encontrarás:
- **Host/URL**: Algo como `xxxxxxxx.s1.eu.hivemq.cloud` o `broker.hivemq.cloud`
- **Port**:
  - `8883` (MQTT con TLS - **RECOMENDADO**)
  - `1883` (MQTT sin TLS - solo para testing)
  - `8884` (WebSocket con TLS)
- **Username**: El que creaste en el paso anterior
- **Password**: La contraseña que creaste

### Paso 5: Actualizar archivos de configuración

Actualiza los archivos `.env` de los siguientes microservicios:

#### a) `microservices/logs-service/.env`

```env
# MongoDB Atlas (ya configurado)
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/logs_db

# MQTT HiveMQ Cloud
MQTT_HOST=xxxxxxxx.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=lsm_mqtt_user
MQTT_PASSWORD=tu_password_seguro
MQTT_USE_TLS=true
```

#### b) `microservices/cognitive-data-service/.env`

```env
# Base de datos (MySQL)
DB_HOST=host.docker.internal
DB_USER=root
DB_PASSWORD=123456
DB_NAME=cognitive_data_db
DB_PORT=3306

# RabbitMQ CloudAMQP (ya configurado)
RABBITMQ_URL=amqps://user:password@shrimp.rmq.cloudamqp.com/vhost

# MQTT HiveMQ Cloud
MQTT_HOST=xxxxxxxx.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=lsm_mqtt_user
MQTT_PASSWORD=tu_password_seguro
MQTT_USE_TLS=true

# Servicios
AUTH_SERVICE_URL=http://auth_service:8000
LOGS_SERVICE_URL=http://logs_service:8009
SESSION_SERVICE_URL=http://session_management_service:8002
```

#### c) `microservices/session-management-service/.env`

```env
# Base de datos (MySQL)
DB_HOST=host.docker.internal
DB_USER=root
DB_PASSWORD=123456
DB_NAME=session_management_db
DB_PORT=3306

# RabbitMQ CloudAMQP (ya configurado)
RABBITMQ_URL=amqps://user:password@shrimp.rmq.cloudamqp.com/vhost

# MQTT HiveMQ Cloud
MQTT_HOST=xxxxxxxx.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=lsm_mqtt_user
MQTT_PASSWORD=tu_password_seguro
MQTT_USE_TLS=true

# Servicios
AUTH_SERVICE_URL=http://auth_service:8000
LOGS_SERVICE_URL=http://logs_service:8009
```

#### d) `microservices/monitoring-alerts-service/.env`

```env
# RabbitMQ CloudAMQP (ya configurado)
RABBITMQ_URL=amqps://user:password@shrimp.rmq.cloudamqp.com/vhost

# MQTT HiveMQ Cloud
MQTT_BROKER_HOST=xxxxxxxx.s1.eu.hivemq.cloud
MQTT_BROKER_PORT=8883
MQTT_USERNAME=lsm_mqtt_user
MQTT_PASSWORD=tu_password_seguro
MQTT_USE_TLS=true

# Otros servicios...
```

### Paso 6: Actualizar docker-compose.yml

Comenta el servicio de MQTT local en `docker-compose.yml`:

```yaml
  # ==========================================
  # MQTT Broker - MIGRADO A HIVEMQ CLOUD
  # ==========================================

  # mqtt_broker:
  #   image: eclipse-mosquitto:2.0
  #   container_name: mqtt_broker
  #   ports:
  #     - "1883:1883"
  #     - "9001:9001"
  #   volumes:
  #     - ./config/mosquitto.conf:/mosquitto/config/mosquitto.conf
  #     - mosquitto_data:/mosquitto/data
  #     - mosquitto_logs:/mosquitto/log
  #   networks:
  #     - lsm_network
```

También **elimina las dependencias** de `mqtt_broker` en el servicio `monitoring_alerts_service`:

**ANTES:**
```yaml
  monitoring_alerts_service:
    build:
      context: ./microservices/monitoring-alerts-service
      dockerfile: Dockerfile
    container_name: monitoring_alerts_service
    env_file:
      - ./microservices/monitoring-alerts-service/.env
    ports:
      - "8003:8003"
    networks:
      - lsm_network
    depends_on:
      rabbitmq:
        condition: service_healthy
      mqtt_broker:              # ← ELIMINAR ESTO
        condition: service_started # ← ELIMINAR ESTO
      auth_service:
        condition: service_started
      logs_service:
        condition: service_started
```

**DESPUÉS:**
```yaml
  monitoring_alerts_service:
    build:
      context: ./microservices/monitoring-alerts-service
      dockerfile: Dockerfile
    container_name: monitoring_alerts_service
    env_file:
      - ./microservices/monitoring-alerts-service/.env
    ports:
      - "8003:8003"
    networks:
      - lsm_network
    depends_on:
      auth_service:
        condition: service_started
      logs_service:
        condition: service_started
```

### Paso 7: Actualizar código de conexión MQTT (si es necesario)

Si tus servicios usan una librería MQTT como `paho-mqtt` (Python) o `mqtt.js` (Node.js), asegúrate de que el código soporte TLS.

**Ejemplo Python (paho-mqtt):**

```python
import paho.mqtt.client as mqtt
import ssl

# Configuración
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "true").lower() == "true"

# Crear cliente
client = mqtt.Client()

# Configurar credenciales
if MQTT_USERNAME and MQTT_PASSWORD:
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# Configurar TLS si está habilitado
if MQTT_USE_TLS:
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)

# Conectar
client.connect(MQTT_HOST, MQTT_PORT, 60)
```

**Ejemplo Node.js (mqtt.js):**

```javascript
const mqtt = require('mqtt');

const options = {
  host: process.env.MQTT_HOST,
  port: parseInt(process.env.MQTT_PORT || '8883'),
  username: process.env.MQTT_USERNAME,
  password: process.env.MQTT_PASSWORD,
  protocol: process.env.MQTT_USE_TLS === 'true' ? 'mqtts' : 'mqtt',
  rejectUnauthorized: true
};

const client = mqtt.connect(options);

client.on('connect', () => {
  console.log('Conectado a HiveMQ Cloud');
});
```

### Paso 8: Probar la conexión

1. Levanta tus servicios:
   ```bash
   docker-compose up -d
   ```

2. Verifica los logs de los servicios que usan MQTT:
   ```bash
   docker logs logs_service
   docker logs cognitive_data_service
   docker logs session_management_service
   docker logs monitoring_alerts_service
   ```

3. Puedes usar la consola de HiveMQ Cloud para ver:
   - Conexiones activas
   - Mensajes publicados/recibidos
   - Suscripciones activas

---

## Checklist de Migración Completa

### RabbitMQ (CloudAMQP)
- [ ] Crear cuenta en CloudAMQP
- [ ] Crear instancia "Little Lemur (Free)"
- [ ] Copiar AMQP URL
- [ ] Actualizar `.env` de `cognitive-data-service`
- [ ] Actualizar `.env` de `session-management-service`
- [ ] Actualizar `.env` de `monitoring-alerts-service`
- [ ] Actualizar `.env` de `analytics-service`
- [ ] Comentar servicio `rabbitmq` en `docker-compose.yml`
- [ ] Eliminar dependencias de `rabbitmq` en microservicios
- [ ] Probar con `docker-compose up -d`

### MQTT (HiveMQ Cloud)
- [ ] Crear cuenta en HiveMQ Cloud
- [ ] Crear cluster Free
- [ ] Crear credenciales de acceso
- [ ] Copiar host, port, username, password
- [ ] Actualizar `.env` de `logs-service`
- [ ] Actualizar `.env` de `cognitive-data-service`
- [ ] Actualizar `.env` de `session-management-service`
- [ ] Actualizar `.env` de `monitoring-alerts-service`
- [ ] Comentar servicio `mqtt_broker` en `docker-compose.yml`
- [ ] Eliminar dependencia de `mqtt_broker` en microservicios
- [ ] Verificar que el código soporte TLS
- [ ] Probar con `docker-compose up -d`

---

## Troubleshooting

### RabbitMQ

**Error: "Connection refused"**
- Verifica que la URL sea correcta (debe empezar con `amqps://`)
- Verifica que no haya firewall bloqueando el puerto 5671/5672

**Error: "Authentication failed"**
- Verifica que las credenciales en la URL sean correctas
- No incluyas caracteres especiales sin codificar en la URL

### MQTT

**Error: "Connection timeout"**
- Verifica que el host y puerto sean correctos
- Verifica que `MQTT_USE_TLS=true` si usas el puerto 8883

**Error: "Authentication failed"**
- Verifica username y password
- Verifica que el usuario tenga permisos de Publish/Subscribe

**Error: "Certificate verification failed"**
- Asegúrate de que `rejectUnauthorized: true` esté configurado
- Si usas Python, verifica que `ssl.CERT_REQUIRED` esté configurado

---

## Notas de Seguridad

1. **NUNCA** commitees los archivos `.env` al repositorio
2. Agrega `.env` al archivo `.gitignore`
3. Usa variables de entorno del sistema o servicios de secrets en producción
4. Rota las contraseñas periódicamente
5. En CloudAMQP, puedes ver métricas y logs en el dashboard
6. En HiveMQ Cloud, puedes monitorear conexiones en tiempo real

---

## Recursos Adicionales

- **CloudAMQP Docs**: https://www.cloudamqp.com/docs/index.html
- **HiveMQ Cloud Docs**: https://docs.hivemq.com/hivemq-cloud/
- **RabbitMQ Python (Pika)**: https://pika.readthedocs.io/
- **Paho MQTT Python**: https://www.eclipse.org/paho/index.php?page=clients/python/index.php
- **MQTT.js**: https://github.com/mqttjs/MQTT.js

---

¡Listo! Una vez que completes estos pasos, tus servicios de RabbitMQ y MQTT estarán corriendo en la nube de forma gratuita.
