import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.settings import (
    SERVICE_PORT,
    SERVICE_NAME,
    AMQP_URL,
    DATABASE_URL,
    REDIS_URL,
    MONITORING_EVENTS_QUEUE,
    RECOMMENDATIONS_QUEUE,
    LOG_SERVICE_QUEUE,
    CACHE_INVALIDATION_QUEUE,
    INTERVENTION_EVALUATIONS_QUEUE,
    ACTIVITY_DETAILS_REQUEST_QUEUE,
    SESSION_CONFIG_REQUEST_QUEUE
)
from src.infrastructure.persistence.database import create_tables, engine
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.intervention_consumer import InterventionConsumer
from src.infrastructure.messaging.cache_invalidation_consumer import CacheInvalidationConsumer
from src.infrastructure.messaging.intervention_evaluation_consumer import InterventionEvaluationConsumer
from src.infrastructure.messaging.queue_validator import validate_service_queues
from src.infrastructure.cache.redis_client import RedisClient
from src.presentation.routes.health_routes import router as health_router
from src.presentation.routes.content_routes import router as content_router

rabbitmq_client = None
redis_client = None
intervention_consumer = None
cache_invalidation_consumer = None
evaluation_consumer = None


def validate_configuration() -> bool:
    errors = []

    if not AMQP_URL:
        errors.append("AMQP_URL no configurado")

    if not DATABASE_URL or "None" in DATABASE_URL:
        errors.append("DATABASE_URL no configurado correctamente")

    if errors:
        print(f"[MAIN] [ERROR] Errores de configuracion:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


def validate_database_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print(f"[MAIN] [INFO] Conexion a base de datos verificada")
        return True
    except Exception as e:
        print(f"[MAIN] [ERROR] Error conectando a base de datos: {str(e)}")
        return False


def validate_rabbitmq_and_queues() -> bool:
    required_queues = [
        {
            "name": MONITORING_EVENTS_QUEUE,
            "require_consumers": False,
            "with_dlq": True
        },
        {
            "name": RECOMMENDATIONS_QUEUE,
            "require_consumers": False,
            "with_dlq": True
        },
        {
            "name": LOG_SERVICE_QUEUE,
            "require_consumers": False,
            "with_dlq": False
        },
        {
            "name": CACHE_INVALIDATION_QUEUE,
            "require_consumers": False,
            "with_dlq": False
        },
        {
            "name": INTERVENTION_EVALUATIONS_QUEUE,
            "require_consumers": False,
            "with_dlq": True
        },
        {
            "name": ACTIVITY_DETAILS_REQUEST_QUEUE,
            "require_consumers": False,
            "with_dlq": True
        },
        {
            "name": SESSION_CONFIG_REQUEST_QUEUE,
            "require_consumers": False,
            "with_dlq": True
        }
    ]

    is_valid, results = validate_service_queues(required_queues, create_missing=True)

    if is_valid:
        print(f"[MAIN] [INFO] Validacion de colas completada:")
        for queue_info in results.get("queues", []):
            status = queue_info.get("status", "unknown")
            name = queue_info.get("name")
            consumers = queue_info.get("consumer_count", 0)
            messages = queue_info.get("message_count", 0)
            print(f"  - {name}: {status} (consumers={consumers}, messages={messages})")
    else:
        print(f"[MAIN] [ERROR] Validacion de colas fallida")
        for error in results.get("errors", []):
            print(f"  - {error}")

    return is_valid


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbitmq_client, redis_client, intervention_consumer, cache_invalidation_consumer, evaluation_consumer

    print(f"[MAIN] [INFO] Iniciando {SERVICE_NAME}...")

    print(f"[MAIN] [INFO] Validando configuracion...")
    if not validate_configuration():
        print(f"[MAIN] [ERROR] Configuracion invalida, abortando inicio")
        sys.exit(1)

    print(f"[MAIN] [INFO] Verificando conexion a base de datos...")
    if not validate_database_connection():
        print(f"[MAIN] [ERROR] No se pudo conectar a la base de datos, abortando inicio")
        sys.exit(1)

    print(f"[MAIN] [INFO] Verificando RabbitMQ y colas...")
    if not validate_rabbitmq_and_queues():
        print(f"[MAIN] [ERROR] No se pudo validar RabbitMQ o las colas, abortando inicio")
        sys.exit(1)

    create_tables()

    rabbitmq_client = RabbitMQClient()
    redis_client = RedisClient()

    intervention_consumer = InterventionConsumer()
    intervention_consumer.start()

    cache_invalidation_consumer = CacheInvalidationConsumer(rabbitmq_client, redis_client)
    cache_invalidation_consumer.start()

    evaluation_consumer = InterventionEvaluationConsumer(rabbitmq_client, redis_client)
    evaluation_consumer.start()

    print(f"[MAIN] [INFO] {SERVICE_NAME} iniciado correctamente en puerto {SERVICE_PORT}")
    yield

    if rabbitmq_client:
        rabbitmq_client.close()
    print(f"[MAIN] [INFO] {SERVICE_NAME} detenido")


app = FastAPI(
    title="Recommendation Service",
    version="2.0.0",
    lifespan=lifespan
)

app.include_router(health_router)
app.include_router(content_router, prefix="/contents", tags=["Contents"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)