from fastapi import APIRouter
from datetime import datetime
import pika
from src.infrastructure.config.settings import (
    AMQP_URL,
    SERVICE_NAME,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DATABASE
)
from src.infrastructure.cache.redis_client import RedisClient
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
            conn.execute("SELECT 1")
        return {
            "status": "ok",
            "host": MYSQL_HOST,
            "port": MYSQL_PORT,
            "database": MYSQL_DATABASE
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_redis() -> dict:
    try:
        redis_client = RedisClient()
        if redis_client._is_available():
            return {"status": "ok"}
        return {"status": "unavailable", "message": "Redis no configurado"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_gemini_circuit_breaker() -> dict:
    try:
        redis_client = RedisClient()
        state = redis_client.get_circuit_breaker_state("gemini")
        if state:
            return {
                "status": state.get("state", "unknown"),
                "failures": state.get("failures", 0)
            }
        return {"status": "closed", "failures": 0}
    except Exception as e:
        return {"status": "unknown", "message": str(e)}


@router.get("/health")
def health_check():
    return {"status": "ok", "service": SERVICE_NAME}


@router.get("/health/detailed")
def health_check_detailed():
    rabbitmq_status = check_rabbitmq()
    database_status = check_database()
    redis_status = check_redis()
    gemini_status = check_gemini_circuit_breaker()

    all_ok = all([
        rabbitmq_status.get("status") == "ok",
        database_status.get("status") == "ok"
    ])

    redis_ok = redis_status.get("status") in ["ok", "unavailable"]
    gemini_ok = gemini_status.get("status") != "open"

    overall_status = "ok"
    if not all_ok:
        overall_status = "error"
    elif not redis_ok or not gemini_ok:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "rabbitmq": rabbitmq_status,
            "database": database_status,
            "redis": redis_status,
            "gemini": gemini_status
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


@router.get("/metrics")
def metrics():
    redis_client = RedisClient()
    gemini_calls = redis_client.get_gemini_calls_count() if redis_client._is_available() else 0
    circuit_state = check_gemini_circuit_breaker()

    return {
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "gemini": {
            "calls_last_minute": gemini_calls,
            "circuit_breaker": circuit_state
        }
    }