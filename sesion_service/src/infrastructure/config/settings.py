import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "session_service")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

AMQP_URL = os.getenv("AMQP_URL")
SERVICE_NAME = os.getenv("SERVICE_NAME", "session-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 3004))
LOG_SERVICE_QUEUE = os.getenv("LOG_SERVICE_QUEUE", "logs")

ACTIVITY_EVENTS_QUEUE = os.getenv("ACTIVITY_EVENTS_QUEUE", "activity_events")
MONITORING_WEBSOCKET_EVENTS_QUEUE = os.getenv("MONITORING_WEBSOCKET_EVENTS_QUEUE", "monitoring_websocket_events")
ACTIVITY_DETAILS_REQUEST_QUEUE = os.getenv("ACTIVITY_DETAILS_REQUEST_QUEUE", "activity_details_request")
ACTIVITY_DETAILS_RESPONSE_QUEUE = os.getenv("ACTIVITY_DETAILS_RESPONSE_QUEUE", "activity_details_response")