import sys
from contextlib import asynccontextmanager
from sqlalchemy import text
from fastapi import FastAPI
from src.infrastructure.config.settings import (
    SERVICE_PORT,
    SERVICE_NAME,
    AMQP_URL,
    DATABASE_URL,
    ACTIVITY_DETAILS_REQUEST_QUEUE,
    ACTIVITY_DETAILS_RESPONSE_QUEUE,
    SESSION_CONFIG_REQUEST_QUEUE,
    SESSION_CONFIG_RESPONSE_QUEUE,
    MONITORING_WEBSOCKET_EVENTS_QUEUE,
    LOG_SERVICE_QUEUE,
    CACHE_INVALIDATION_QUEUE
)
from src.infrastructure.persistence.database import create_tables, engine
from src.infrastructure.messaging.rabbitmq_client import RabbitMQClient
from src.infrastructure.messaging.activity_details_consumer import ActivityDetailsConsumer
from src.infrastructure.messaging.websocket_event_consumer import WebsocketEventConsumer
from src.infrastructure.messaging.session_config_consumer import SessionConfigConsumer
from src.infrastructure.messaging.queue_validator import validate_service_queues
from src.presentation.controllers.session_controller import router as session_router
from src.presentation.controllers.activity_controller import router as activity_router
from src.presentation.routes.health_routes import router as health_router

rabbitmq_client = None
activity_details_consumer = None
websocket_event_consumer = None
session_config_consumer = None


def validate_configuration() -> bool:
    errors = []

    if not AMQP_URL:
        errors.append("AMQP_URL no configurado")

    if not DATABASE_URL or "None" in DATABASE_URL:
        errors.append("DATABASE_URL no configurado correctamente")

    required_queues = [
        ("ACTIVITY_DETAILS_REQUEST_QUEUE", ACTIVITY_DETAILS_REQUEST_QUEUE),
        ("ACTIVITY_DETAILS_RESPONSE_QUEUE", ACTIVITY_DETAILS_RESPONSE_QUEUE),
        ("SESSION_CONFIG_REQUEST_QUEUE", SESSION_CONFIG_REQUEST_QUEUE),
        ("SESSION_CONFIG_RESPONSE_QUEUE", SESSION_CONFIG_RESPONSE_QUEUE),
        ("MONITORING_WEBSOCKET_EVENTS_QUEUE", MONITORING_WEBSOCKET_EVENTS_QUEUE)
    ]

    for name, value in required_queues:
        if not value:
            errors.append(f"{name} no configurado")

    if errors:
        print(f"[MAIN] [ERROR] Errores de configuracion:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


def validate_database_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[MAIN] [INFO] Conexion a base de datos verificada")
        return True
    except Exception as e:
        print(f"[MAIN] [ERROR] Error conectando a base de datos: {str(e)}")
        return False


def validate_rabbitmq_and_queues() -> bool:
    required_queues = [
        {"name": ACTIVITY_DETAILS_REQUEST_QUEUE, "required": True},
        {"name": ACTIVITY_DETAILS_RESPONSE_QUEUE, "required": False},
        {"name": SESSION_CONFIG_REQUEST_QUEUE, "required": True},
        {"name": SESSION_CONFIG_RESPONSE_QUEUE, "required": False},
        {"name": MONITORING_WEBSOCKET_EVENTS_QUEUE, "required": True},
        {"name": LOG_SERVICE_QUEUE, "required": True},
        {"name": CACHE_INVALIDATION_QUEUE, "required": True}
    ]

    is_valid, results = validate_service_queues(required_queues, create_missing=True)

    print(f"[MAIN] [INFO] Validacion de colas completada:")
    for queue in results.get("queues", []):
        status = queue.get("status", "unknown")
        consumers = queue.get("consumers", 0)
        messages = queue.get("messages", 0)
        print(f"  - {queue['name']}: {status} (consumers={consumers}, messages={messages})")

    for warning in results.get("warnings", []):
        print(f"[MAIN] [WARNING] {warning}")

    for error in results.get("errors", []):
        print(f"  - {error}")

    return is_valid


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbitmq_client, activity_details_consumer, websocket_event_consumer, session_config_consumer

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

    activity_details_consumer = ActivityDetailsConsumer(rabbitmq_client)
    activity_details_consumer.start()

    websocket_event_consumer = WebsocketEventConsumer()
    websocket_event_consumer.start()

    session_config_consumer = SessionConfigConsumer(rabbitmq_client)
    session_config_consumer.start()

    print(f"[MAIN] [INFO] {SERVICE_NAME} iniciado correctamente en puerto {SERVICE_PORT}")
    yield

    if rabbitmq_client:
        rabbitmq_client.close()
    print(f"[MAIN] [INFO] {SERVICE_NAME} detenido")


app = FastAPI(
    title="Session Service",
    version="2.0.0",
    lifespan=lifespan
)

app.include_router(health_router)
app.include_router(session_router, prefix="/sessions", tags=["Sessions"])
app.include_router(activity_router, prefix="/activities", tags=["Activities"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)