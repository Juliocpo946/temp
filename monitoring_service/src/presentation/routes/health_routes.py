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
from src.infrastructure.websocket.connection_manager import ConnectionManager

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
            return {"status": "ok", "instance_id": redis_client.get_instance_id()}
        return {"status": "unavailable", "message": "Redis no configurado"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_websocket_connections() -> dict:
    try:
        manager = ConnectionManager()
        return {
            "status": "ok",
            "active_connections": manager.connection_count
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_backpressure_summary() -> dict:
    try:
        manager = ConnectionManager()
        all_metrics = manager.get_all_backpressure_metrics()
        
        total_received = sum(m.get("frames_received", 0) for m in all_metrics.values())
        total_processed = sum(m.get("frames_processed", 0) for m in all_metrics.values())
        total_dropped = sum(m.get("frames_dropped", 0) for m in all_metrics.values())
        total_throttles = sum(m.get("throttle_events", 0) for m in all_metrics.values())
        throttled_connections = sum(1 for m in all_metrics.values() if m.get("is_throttled", False))
        
        problematic = manager.get_problematic_connections()
        
        return {
            "total_connections": len(all_metrics),
            "total_frames_received": total_received,
            "total_frames_processed": total_processed,
            "total_frames_dropped": total_dropped,
            "total_throttle_events": total_throttles,
            "currently_throttled": throttled_connections,
            "problematic_connections": problematic,
            "drop_rate": round(total_dropped / total_received * 100, 2) if total_received > 0 else 0
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
    redis_status = check_redis()
    websocket_status = check_websocket_connections()
    backpressure_status = get_backpressure_summary()

    all_ok = all([
        rabbitmq_status.get("status") == "ok",
        database_status.get("status") == "ok",
        websocket_status.get("status") == "ok"
    ])

    redis_ok = redis_status.get("status") in ["ok", "unavailable"]
    
    has_backpressure_issues = backpressure_status.get("drop_rate", 0) > 5 or \
                              backpressure_status.get("currently_throttled", 0) > 0

    overall_status = "ok"
    if not all_ok:
        overall_status = "error"
    elif not redis_ok or has_backpressure_issues:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "rabbitmq": rabbitmq_status,
            "database": database_status,
            "redis": redis_status,
            "websocket": websocket_status,
            "backpressure": backpressure_status
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
    manager = ConnectionManager()
    redis_client = RedisClient()
    backpressure = get_backpressure_summary()
    ws_metrics = redis_client.get_websocket_metrics() if redis_client._is_available() else {}

    return {
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "websocket": {
            "active_connections": manager.connection_count,
            "frames_sent": ws_metrics.get("sent", 0),
            "frames_failed": ws_metrics.get("failed", 0),
            "frames_dropped": ws_metrics.get("dropped", 0)
        },
        "backpressure": backpressure,
        "instance": {
            "id": redis_client.get_instance_id() if redis_client._is_available() else "unknown"
        }
    }


@router.get("/metrics/connections")
def connection_metrics():
    manager = ConnectionManager()
    all_metrics = manager.get_all_backpressure_metrics()
    
    connections = []
    for activity_uuid, metrics in all_metrics.items():
        state = manager.get_state(activity_uuid)
        connections.append({
            "activity_uuid": activity_uuid,
            "session_id": state.session_id if state else None,
            "is_ready": state.is_ready if state else False,
            "metrics": metrics
        })
    
    return {
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "connections": connections
    }