from fastapi import APIRouter
from datetime import datetime
import pika
from sqlalchemy import text  # <--- AGREGAR ESTO
from src.infrastructure.config.settings import (
    AMQP_URL,
    SERVICE_NAME,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DATABASE
)
from src.infrastructure.persistence.database import engine

router = APIRouter()


def check_rabbitmq() -> dict:
    try:
        parameters = pika.URLParameters(AMQP_URL)
        parameters.socket_timeout = 5
        connection = pika.BlockingConnection(parameters)
        connection.close()
        return {"status": "ok", "message": "Conectado"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_database() -> dict:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "host": MYSQL_HOST,
            "port": MYSQL_PORT,
            "database": MYSQL_DATABASE
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/health")
def health_check():
    return {"status": "ok", "service": SERVICE_NAME}


@router.get("/health/detailed")
def health_check_detailed():
    rabbitmq_status = check_rabbitmq()
    database_status = check_database()

    all_ok = all([
        rabbitmq_status.get("status") == "ok",
        database_status.get("status") == "ok"
    ])

    return {
        "status": "ok" if all_ok else "degraded",
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "rabbitmq": rabbitmq_status,
            "database": database_status
        }
    }


@router.get("/ready")
def readiness_check():
    rabbitmq_status = check_rabbitmq()
    database_status = check_database()

    is_ready = (
            rabbitmq_status.get("status") == "ok" and
            database_status.get("status") == "ok"
    )

    if is_ready:
        return {"status": "ready", "service": SERVICE_NAME}

    return {
        "status": "not_ready",
        "service": SERVICE_NAME,
        "issues": {
            "rabbitmq": rabbitmq_status if rabbitmq_status.get("status") != "ok" else None,
            "database": database_status if database_status.get("status") != "ok" else None
        }
    }